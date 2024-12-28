from typing import Dict, Any
from twilio.twiml.messaging_response import MessagingResponse
from ..models import WhatsAppUser, RawMessage
from ..ai_services.nlp_processor import is_gym_log
from ..dao.user_dao import UserDAO
from ..dao.body_history_dao import BodyHistoryDAO
from .message_flow import is_hello_message
from ..ai_services.nlp_processor import is_name_response

def handle_welcome_and_details(user: WhatsAppUser) -> MessagingResponse:
    """
    Generate combined welcome and details request based on user state
    """
    response = MessagingResponse()
    
    # First message - Welcome
    msg1 = response.message()
    msg1.body("""Hello! Welcome to GymTracker! 💪

Track your workouts in natural language, monitor progress, and achieve your fitness goals.""")
    
    # Second message - Based on user state
    msg2 = response.message()
    if not user.name:
        msg2.body("Hi,What's your name?")
    elif not BodyHistoryDAO.has_activity(user):
        msg2.body("Please select your activity level:")
        msg2.options([
            "Sedentary (little or no exercise)",
            "Lightly Active (1-3 days/week)",
            "Moderately Active (3-5 days/week)",
            "Very Active (6-7 days/week)",
            "Extra Active (very active & physical job)"
        ])
    elif not BodyHistoryDAO.has_measurements(user):
        msg2.body("""Please provide your height and weight:
- Height (in cm)
- Weight (in kg)

Format: "height: 170, weight: 70"

You can also send a progress photo (optional).""")
    else:
        metrics = BodyHistoryDAO.get_latest_metrics(user)
        msg2.body(f"Welcome back! Your current stats:\nHeight: {metrics.get('height')}cm\nWeight: {metrics.get('weight')}kg\n\nYou can start logging your workouts!")
        
    return response

def handle_name_retry(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    msg = response.message()
    msg.body("Hi,Please provide your name :)")
    return response

def handle_name_success(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    msg = response.message()
    msg.body(f"Thanks {user.name}! Now, let me help you track your fitness journey.")
    return response

def handle_activity_retry(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    msg = response.message()
    msg.body("Hi,Please provide your name :)")
    return response

def handle_message(form_data: Dict[str, Any], user: WhatsAppUser) -> MessagingResponse:
    """
    Main message handler using Twilio's format
    """
    phone_number = form_data.get('from')
    message_body = form_data.get('body', '')

    # Store raw message
    RawMessage.objects.create(
        phone_number=phone_number,
        message=message_body,
        incoming=True
    )

    # If hello message, handle welcome flow
    if is_hello_message(message_body):
        return handle_welcome_and_details(user)

    # If no name, check if this is a name response
    if not user.name:
        is_name, extracted_name = is_name_response(message_body, user)
        if is_name:
            UserDAO.update_user_details(phone_number, name=extracted_name)
        else:
            return handle_name_retry(user)
    else:
        print(f"User already has name: {user.name}")

    # If no activity, check if this is an activity selection
    if not BodyHistoryDAO.has_activity(user):
        activity_map = {
            "sedentary": "Sedentary (little or no exercise)",
            "light": "Lightly Active (1-3 days/week)",
            "moderate": "Moderately Active (3-5 days/week)",
            "very": "Very Active (6-7 days/week)",
            "extra": "Extra Active (very active & physical job)"
        }
        selected_activity = message_body.strip().lower()
        if selected_activity in activity_map:
            BodyHistoryDAO.create_entry(user, activity=selected_activity)
        else:
            return handle_activity_retry(user)
    else:
        print(f"User already has activity: {BodyHistoryDAO.get_latest_metrics(user).get('activity')}")

    # If no measurements, check if this is height/weight input
    if not BodyHistoryDAO.has_measurements(user):
        import re
        height_match = re.search(r'height:\s*(\d+)', message_body.lower())
        weight_match = re.search(r'weight:\s*(\d+)', message_body.lower())
        
        if height_match and weight_match:
            height = float(height_match.group(1))
            weight = float(weight_match.group(1))
            if 100 <= height <= 250 and 30 <= weight <= 200:  # Basic validation
                BodyHistoryDAO.create_entry(user, height=height, weight=weight)
                return handle_welcome_and_details(user)

    # Handle other message types
    if is_gym_log(message_body):
        response = MessagingResponse()
        msg = response.message()
        msg.body("Logging your workout...")
        return response
    
    # Default response
    response = MessagingResponse()
    msg = response.message()
    msg.body("I didn't understand that. Try sending a workout log or type 'help' for options.")
    return response

