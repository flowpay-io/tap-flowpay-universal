import pytest

@pytest.fixture
def api_key_config():
    """Fixture that provides a valid API Key config."""
    return {
        "url": "https://test.flowpay.com/api/v1/orders",
        "start_date": "2022-01-01T00:00:00Z",
        "merchant_id": "test_merchant",
        "auth_type": "API_KEY",
        "api_key": "test_api_key",
    }

@pytest.fixture
def orders_response():
    """Fixture to simulate a valid orders response wrapped in 'data'."""
    return {
        "data": [
            {
                "id": "Bj60hk9kkPVAH9QBXr2a",
                "createdAt": "2024-01-21T19:19:19Z",
                "updatedAt": "2024-01-21T19:19:19Z",
                "status": "DELIVERED",
                "delivery": "CARRIER",
                "payment": "CASH",
                "customerId": "Bj60hk9kkPVAH9QBXr2a",
                "customerName": "Customer Name",
                "currency": "USD",
                "totalPrice": 59.99,
                "totalDiscount": 10,
                "totalShipping": 10,
                "totalTax": 10,
                "items": [
                    {
                        "productId": "Bj60hk9kkPVAH9QBXr2a",
                        "productName": "Product Title",
                        "quantity": 1,
                        "unitPrice": 49.99,
                        "totalPrice": 49.99,
                        "discountAmount": 10,
                        "taxAmount": 10
                    }
                ],
                "billingAddress": {
                    "line1": "Rooseveltova 613/38",
                    "city": "Praha 6",
                    "country": "CZ",
                    "zip": "16000"
                },
                "shippingAddress": {
                    "line1": "Rooseveltova 613/38",
                    "city": "Praha 6",
                    "country": "CZ",
                    "zip": "16000"
                }
            }
        ]
    }


@pytest.fixture
def orders_response_plain_array():
    """Fixture to simulate a valid orders response as plain array."""
    return [
        {
            "id": "plain-array-id-123",
            "createdAt": "2024-01-21T19:19:19Z",
            "updatedAt": "2024-01-21T19:19:19Z",
            "status": "DELIVERED",
            "delivery": "CARRIER",
            "payment": "CARD",
            "customerId": "customer-123",
            "customerName": "Plain Array Customer",
            "currency": "EUR",
            "totalPrice": 99.99,
            "totalDiscount": 5,
            "totalShipping": 5,
            "totalTax": 5,
            "items": [],
            "billingAddress": {
                "line1": "Test Street 1",
                "city": "Test City",
                "country": "CZ",
                "zip": "12345"
            },
            "shippingAddress": {
                "line1": "Test Street 1",
                "city": "Test City",
                "country": "CZ",
                "zip": "12345"
            }
        }
    ]


@pytest.fixture
def sample_order():
    """Single order record for reuse."""
    return {
        "id": "test-order-id",
        "createdAt": "2024-01-21T19:19:19Z",
        "updatedAt": "2024-01-21T19:19:19Z",
        "status": "DELIVERED",
        "delivery": "CARRIER",
        "payment": "CARD",
        "customerId": "customer-123",
        "customerName": "Test Customer",
        "currency": "EUR",
        "totalPrice": 10.00,
    }

