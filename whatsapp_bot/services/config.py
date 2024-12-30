import os

# Environment-based configuration
IS_DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
ENVIRONMENT = 'test_mode' if IS_DEBUG else 'live_mode'

# Product IDs for different environments
DODO_PRODUCT_IDS = {
    'test_mode': {
        "10": "pdt_dalSRa7gwzxF3IAVkXDZs",
        "20": "test_prod_456",
        # Add more test product IDs as needed
    },
    'live_mode': {
        "10": "prod_123",
        "20": "prod_456",
        # Add more production product IDs as needed
    }
}

def get_product_ids():
    """Get the appropriate product IDs based on environment"""
    return DODO_PRODUCT_IDS[ENVIRONMENT]
