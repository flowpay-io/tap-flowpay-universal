"""Tests standard tap features."""

import datetime
import pytest

from tap_flowpay_universal.tap import TapFlowpayUniversal

SAMPLE_CONFIG = {
    "start_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
    "merchant_id": "test_merchant",
    "url": "https://test.flowpay.com/api/v1/orders",
    "auth_type": "API_KEY",
    "api_key": "test_api_key",
}


def test_tap_initialization():
    """Test that the tap initializes correctly with valid config."""
    tap = TapFlowpayUniversal(config=SAMPLE_CONFIG)
    assert tap.name == "tap-flowpay-universal"


def test_tap_discovers_streams():
    """Test that the tap discovers the expected streams."""
    tap = TapFlowpayUniversal(config=SAMPLE_CONFIG)
    streams = tap.discover_streams()
    assert len(streams) == 1
    assert streams[0].name == "orders"


def test_tap_missing_auth_type():
    """Test that tap raises error when auth_type is missing."""
    invalid_config = {
        "start_date": "2022-01-01",
        "merchant_id": "test_merchant",
        "url": "https://test.flowpay.com/api/v1/orders",
        # Missing auth_type
    }
    with pytest.raises(Exception):
        tap = TapFlowpayUniversal(config=invalid_config)
        # Force stream initialization to trigger auth check
        list(tap.discover_streams())[0].authenticator


def test_tap_oauth_config_missing_fields():
    """Test that OAuth config raises error when required fields are missing."""
    incomplete_oauth_config = {
        "start_date": "2022-01-01",
        "merchant_id": "test_merchant",
        "url": "https://test.flowpay.com/api/v1/orders",
        "auth_type": "JWT",
        "client_id": "test_client_id",
        # Missing: client_secret, audience, token_endpoint_url
    }
    with pytest.raises(Exception):
        tap = TapFlowpayUniversal(config=incomplete_oauth_config)
        list(tap.discover_streams())[0].authenticator


def test_tap_api_key_config_missing_key():
    """Test that API Key config raises error when api_key is missing."""
    incomplete_api_key_config = {
        "start_date": "2022-01-01",
        "merchant_id": "test_merchant",
        "url": "https://test.flowpay.com/api/v1/orders",
        "auth_type": "API_KEY",
        # Missing: api_key
    }
    with pytest.raises(Exception):
        tap = TapFlowpayUniversal(config=incomplete_api_key_config)
        list(tap.discover_streams())[0].authenticator
