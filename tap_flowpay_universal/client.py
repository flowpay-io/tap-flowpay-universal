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

    # Update this value if necessary or override `parse_response`.
    records_jsonpath = "$[*]"
    
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
        records = data if isinstance(data, list) else data.get("data", [])
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
        
        Raises an error if API returned data but extraction yields nothing.
        """
        data = response.json()
        
        # Calculate response size for validation
        response_size = len(response.content)
        
        # Auto-detect format and extract records
        if isinstance(data, list):
            # Plain array format: [{...}, {...}]
            records = data
        elif isinstance(data, dict) and "data" in data:
            # Wrapped format: {"data": [{...}, {...}]}
            records = data.get("data", [])
        else:
            records = []
        
        # Fail if API returned data but we extracted nothing
        if response_size > 100 and len(records) == 0:
            raise RuntimeError(
                f"API returned {response_size} bytes but 0 records were extracted. "
                f"Response format may not be supported. Response preview: {str(data)[:500]}"
            )
        
        self.logger.info(f"Extracted {len(records)} records from response")
        
        for record in records:
            yield record
    
    