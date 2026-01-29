"""REST client handling, including FlowpayUniversalStream base class."""

import logging
from functools import lru_cache
from urllib.parse import urlparse

from singer_sdk.streams import RESTStream

from tap_flowpay_universal.auth import MissingCredentialConfigException, OAuth2Authenticator, ApiKeyAuthenticator


class MissingConfig(Exception):
    pass


class FlowpayUniversalStream(RESTStream):
    """FlowpayUniversal stream class."""

    page_size = 100


    def __init__(self, *args, **kwargs):
        """Initialize the FlowpayUniversal stream.
        
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
            
        Raises:
            MissingConfig: If the URL is not provided in the config.
        """
        super().__init__(*args, **kwargs)
        
        url = self.config.get("url")
        if not url:
            raise MissingConfig("The 'url' parameter is required in config file.")
            
        parsed_url = urlparse(url.rstrip('/'))
        
        # Extract the last path component as orders_path
        path_components = [p for p in parsed_url.path.split('/') if p]
        orders_path = f"/{path_components[-1]}" if path_components else ""
        
        # Construct base URL by removing orders_path
        base_path = '/'.join(path_components[:-1]) if path_components else ''
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        if base_path:
            base_url = f"{base_url}/{base_path}"
                
        self._config["orders_path"] = orders_path
        self._base_url = base_url

    @property
    def url_base(self) -> str:
        return self._base_url

    @property
    @lru_cache(maxsize=None)
    def authenticator(self):
        """Return a new authenticator object."""
        auth_type = self._tap.config.get("auth_type")
        
        if not auth_type:
            raise MissingConfig("The 'auth_type' parameter is required in config file.")
            
        if auth_type == "JWT":
            return OAuth2Authenticator(self)
        elif auth_type == "API_KEY":
            return ApiKeyAuthenticator(self)
        else:
            raise MissingConfig("Auth type must be either 'JWT' or 'API_KEY'")

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed."""
        headers = {}
        headers["Content-Type"] = "application/json"
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    def _extract_records(self, data):
        """Extract records from response data, auto-detecting format.
        
        Supports two formats:
        - Plain array: [{...}, {...}]
        - Wrapped: {"data": [{...}, {...}], ...}
        
        Args:
            data: Parsed JSON response data
            
        Returns:
            tuple: (records list, format_recognized bool)
        """
        if isinstance(data, list):
            return data, True
        elif isinstance(data, dict) and "data" in data:
            return data.get("data", []), True
        else:
            return [], False

    def get_next_page_token(self, response, previous_token):
        """Return next page token supporting both cursor and count-based pagination.
        
        Pagination modes (per spec):
        1. Cursor-based: If API returns `next_page` in response, use that value
        2. Count-based: If no `next_page`, increment page number while response 
           contains exactly `page_size` records
        
        Args:
            response: The HTTP response object
            previous_token: The previous page token (cursor or page number)
            
        Returns:
            Next page token, or None if no more pages
        """
        data = response.json()
        
        # Mode 1: Cursor-based pagination - check for next_page in response
        if isinstance(data, dict) and "next_page" in data:
            return data.get("next_page")  # Returns None if next_page is null
        
        # Mode 2: Count-based pagination - check response size
        records, _ = self._extract_records(data)
        record_count = len(records)
        
        if record_count > self.page_size:
            # API returned more than requested - ignoring pagination, stop
            self.logger.info(f"API returned {record_count} records (requested {self.page_size}), pagination not supported")
            return None
        
        if record_count < self.page_size:
            # Fewer records than page_size means no more pages
            return None
        
        # Exactly page_size records - more pages may be available
        current_page = previous_token if isinstance(previous_token, int) else 0
        return current_page + 1

    def get_url_params(self, context, next_page_token):
        params: dict = {}
        if not self._tap.config.get("merchant_id"):
            raise MissingConfig("The request requires 'merchant_id' in config file.")
        params["merchantId"] = self._config.get("merchant_id")

        if self._config.get("tenant_id"):
            params["tenantId"] = self._config.get("tenant_id")

        # Always send page parameter (0-based per spec)
        if next_page_token is not None:
            params["page"] = next_page_token
        else:
            params["page"] = 0
        
        params["size"] = self.page_size
        return params

    def prepare_request(self, context, next_page_token):
        """Prepare the request and log the full URL."""
        request = super().prepare_request(context, next_page_token)
        self.logger.info(f"Request URL: {request.url}")
        return request

    def parse_response(self, response):
        """Parse the response, auto-detecting format (plain array or wrapped in 'data').
        
        Raises an error if response format is unrecognized (not a list or dict with 'data' key).
        """
        data = response.json()
        records, format_recognized = self._extract_records(data)
        
        # Only fail if format is unrecognized and response has content
        # Legitimate empty responses (e.g., {"data": [], "total": 0}) are valid
        if not format_recognized and len(response.content) > 100:
            raise RuntimeError(
                f"API returned {len(response.content)} bytes but response format is not supported. "
                f"Expected a list or dict with 'data' key. Response preview: {str(data)[:500]}"
            )
        
        self.logger.info(f"Extracted {len(records)} records from response")
        
        for record in records:
            yield record
    
    