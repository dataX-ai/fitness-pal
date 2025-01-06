import os
import pandas as pd
import json

# Environment-based configuration
IS_DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

############################
# BMI Configuration
############################

BMI_TARGETS = {
    'lean': 20.5,      # Slim and Defined
    'athletic': 23.0,  # Muscular and Balanced
    'bulk': 25.0       # Large and Powerful
}

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
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+12316255796' #'whatsapp:+14155238886'


############################
# Whatsapp Templates
############################

WHATSAPP_PAYMENT_SUCCESS_TEMPLATE_SID = "HX7b409bcca6dc22fe1a18110f76497f6d"
WHATSAPP_PAYMENT_FAILED_TEMPLATE_SID = "HX8b1c7c75eb2bb5446d97a2a4d3c819fb"
WHATSAPP_GOAL_TEMPLATE_SID = "HX4707aded3e66fc659fca7d4a28556efc"
WHATSAPP_ACTIVITY_TEMPLATE_SID = "HX924f53aed72555c48b8f5f402a615098"

############################
# Subscription Configuration
############################

MAX_FREE_MESSAGES_PER_DAY = int(os.getenv('MAX_FREE_MESSAGES_PER_DAY', '3'))

############################
# Exercise List
############################

EXERCISE_LIST_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'utils', 'exercise_list.csv')
EXERCISE_LEVEL_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'utils', 'exercise_range_kg.json')
try:
    EXERCISE_LIST_DF = pd.read_csv(EXERCISE_LIST_CSV_PATH)
    string_columns = EXERCISE_LIST_DF.select_dtypes(include=['object']).columns
    EXERCISE_LIST_DF[string_columns] = EXERCISE_LIST_DF[string_columns].apply(lambda x: x.str.lower())
except Exception as e:
    raise Exception(f"Error loading exercise list CSV: {e}")

try:
    with open(EXERCISE_LEVEL_JSON_PATH) as f:
        data = json.load(f)
        # Convert all exercise names to lowercase
        EXERCISE_LEVEL_JSON = {k.lower(): v for k, v in data.items()}
except Exception as e:
    raise Exception(f"Error loading exercise level JSON: {e}")

EXERCISE_LEVEL_INTENSITY_MAPPING = {
    'level1': 10,
    'level2': 15,
    'level3': 25,
}

MUSCLE_GROUP_MERGING_MAP = {
    'bicep': 'arms',
    'triceps': 'arms',
    'forearm flexors & grip': 'arms',
    'forearm extensor': 'arms',
    'biceps': 'arms',
    
    'leg': 'legs',
    'glute': 'legs',
    'calves': 'legs',
    'quadriceps': 'legs',
    'hamstrings': 'legs',
    'glutes': 'legs',
    
    'shoulder': 'shoulders',
    'shoulders': 'shoulders',
    
    'ab': 'abs',
    'abs': 'abs'
}