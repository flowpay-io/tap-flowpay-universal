from unittest.mock import patch, MagicMock
import pytest
from tap_flowpay_universal.tap import TapFlowpayUniversal
from tap_flowpay_universal.streams import OrdersStream


def test_orders_stream_parsing_wrapped_response(orders_response, api_key_config):
    """Test parsing orders from wrapped response {"data": [...]}."""
    with patch("singer_sdk.streams.RESTStream._request") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = orders_response

        stream = OrdersStream(tap=TapFlowpayUniversal(config=api_key_config))
        records = list(stream.get_records(None))

        assert len(records) == 1
        record = records[0]
        assert record["id"] == "Bj60hk9kkPVAH9QBXr2a"
        assert record["totalPrice"] == 59.99
        assert record["billingAddress"]["city"] == "Praha 6"


def test_orders_stream_parsing_plain_array(orders_response_plain_array, api_key_config):
    """Test parsing orders from plain array response [...] with auto-detection."""
    with patch("singer_sdk.streams.RESTStream._request") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = orders_response_plain_array

        stream = OrdersStream(tap=TapFlowpayUniversal(config=api_key_config))
        records = list(stream.get_records(None))

        assert len(records) == 1
        record = records[0]
        assert record["id"] == "plain-array-id-123"
        assert record["totalPrice"] == 99.99
        assert record["customerName"] == "Plain Array Customer"


def test_parse_response_fails_on_unrecognized_format(api_key_config):
    """Test that parse_response raises RuntimeError when response format is unrecognized."""
    stream = OrdersStream(tap=TapFlowpayUniversal(config=api_key_config))
    
    # Mock response with data but unsupported format (no "data" key)
    mock_response = MagicMock()
    mock_response.json.return_value = {"unsupported_key": [{"id": "123"}]}
    mock_response.content = b'{"unsupported_key": [{"id": "123"}]}' * 10  # > 100 bytes
    
    with pytest.raises(RuntimeError) as exc_info:
        list(stream.parse_response(mock_response))
    
    assert "response format is not supported" in str(exc_info.value)


def test_pagination_uses_nextPage_cursor_when_provided(api_key_config, sample_order):
    """Test that pagination uses nextPage value from API response (cursor-based)."""
    stream = OrdersStream(tap=TapFlowpayUniversal(config=api_key_config))
    
    # Simulate API returning records with nextPage cursor
    records = [sample_order.copy() for _ in range(100)]
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": records, "nextPage": 2}
    
    next_token = stream.get_next_page_token(mock_response, None)
    
    # Should return 2 (the nextPage value from API)
    assert next_token == 2


def test_pagination_stops_when_nextPage_is_null(api_key_config, sample_order):
    """Test that pagination stops when nextPage is null (last page, cursor-based)."""
    stream = OrdersStream(tap=TapFlowpayUniversal(config=api_key_config))
    
    # Simulate API returning records with nextPage: null (last page)
    records = [sample_order.copy() for _ in range(50)]
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": records, "nextPage": None}
    
    next_token = stream.get_next_page_token(mock_response, 1)
    
    # Should return None because nextPage is null
    assert next_token is None


def test_pagination_stops_when_records_exceed_page_size(api_key_config, sample_order):
    """Test that pagination stops when API returns more records than page_size (wrapped format)."""
    stream = OrdersStream(tap=TapFlowpayUniversal(config=api_key_config))
    
    # Simulate API returning 500 records when page_size is 100 (wrapped format)
    many_records = [sample_order.copy() for _ in range(500)]
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": many_records}
    
    next_token = stream.get_next_page_token(mock_response, None)
    
    # Should return None (stop pagination) because 500 > 100
    assert next_token is None


def test_pagination_continues_when_records_equal_page_size(api_key_config, sample_order):
    """Test that pagination continues when records == page_size (plain array format)."""
    stream = OrdersStream(tap=TapFlowpayUniversal(config=api_key_config))
    
    # Simulate API returning exactly page_size records (plain array format)
    exact_records = [sample_order.copy() for _ in range(stream.page_size)]
    
    mock_response = MagicMock()
    mock_response.json.return_value = exact_records
    
    next_token = stream.get_next_page_token(mock_response, 0)
    
    # Should return 1 (next page) because 100 == 100
    assert next_token == 1


def test_pagination_stops_when_records_less_than_page_size(api_key_config, sample_order):
    """Test that pagination stops when records < page_size (last page, wrapped format)."""
    stream = OrdersStream(tap=TapFlowpayUniversal(config=api_key_config))
    
    # Simulate API returning fewer than page_size records (wrapped format)
    few_records = [sample_order.copy() for _ in range(50)]
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": few_records}
    
    next_token = stream.get_next_page_token(mock_response, 0)
    
    # Should return None (stop pagination) because 50 < 100
    assert next_token is None