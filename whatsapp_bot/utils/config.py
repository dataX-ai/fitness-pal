import os

# Environment-based configuration
IS_DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

############################
# Dodo Configuration
############################

DODO_ENVIRONMENT = 'test_mode' if IS_DEBUG else 'live_mode'
DODO_WEBHOOK_SECRET = os.getenv('DODO_WEBHOOK_SECRET')

# Product IDs for different environments
DODO_PRODUCT_IDS = {
    'test_mode': {
        "9.99": "pdt_dalSRa7gwzxF3IAVkXDZs",
        "29.99": "test_prod_456",
        "99": "pdt_dalSRa7gwzxF3IAVkXDZs",
        "299": "test_prod_456",
        # Add more test product IDs as needed
    },
    'live_mode': {
        "10": "prod_123",
        "20": "prod_456",
        # Add more production product IDs as needed
    }
}

DODO_SUBSCRIPTION_NAMES ={
    "9.99": "Pro Athlete",
    "29.99": "Elite Training",
    "99": "Pro Athlete",
    "299": "Elite Training",
}

def get_product_ids():
    """Get the appropriate product IDs based on environment"""
    return DODO_PRODUCT_IDS[DODO_ENVIRONMENT]

############################
# Twilio Configuration
############################

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'


############################
# Whatsapp Templates
############################

WHATSAPP_PAYMENT_SUCCESS_TEMPLATE_SID = "HX7b409bcca6dc22fe1a18110f76497f6d"
WHATSAPP_PAYMENT_FAILED_TEMPLATE_SID = "HX8b1c7c75eb2bb5446d97a2a4d3c819fb"
