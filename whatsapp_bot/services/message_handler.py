from typing import Dict, Any
from twilio.twiml.messaging_response import MessagingResponse
from ..models import WhatsAppUser, RawMessage
from ..ai_services.nlp_processor import is_gym_log

def handle_welcome_message() -> MessagingResponse:
    """
    Generate welcome template message with app introduction using Twilio's format
    """
    response = MessagingResponse()
    msg = response.message()
    msg.body("""Welcome to GymTracker! 💪

Track your workouts in natural language, monitor progress, and achieve your fitness goals.""")
    return response

def add_weight_message(response: MessagingResponse):
    msg = response.message()

def request_user_details() -> MessagingResponse:
    """
    Send interactive message requesting user details using Twilio's format
    """
    response = MessagingResponse()
    
    # First message - Activity level
    msg1 = response.message()
    msg1.body("Please select your activity level:")
    msg1.options([
        "Sedentary (little or no exercise)",
        "Lightly Active (1-3 days/week)",
        "Moderately Active (3-5 days/week)",
        "Very Active (6-7 days/week)",
        "Extra Active (very active & physical job)"
    ])
    
    # Second message - Height and weight instructions
    msg2 = response.message()
    msg2.body("""After selecting your activity level, please reply with your:
- Height (in cm)
- Weight (in kg)

Format: "height: 170, weight: 70"

You can also send a progress photo (optional).""")
    return response

def handle_message(form_data: Dict[str, Any]) -> MessagingResponse:
    """
    Main message handler using Twilio's format
    """
    phone_number = form_data.get('from')
    message_body = form_data.get('body', '')
    
    # Store raw message
    RawMessage.objects.create(
        phone_number=phone_number,
        message=message_body
    )
    
    # Check if user exists
    user, created = WhatsAppUser.objects.get_or_create(phone_number=phone_number)
    
    # If new user or hello message
    if created or is_hello_message(message_body):
        # Send welcome message and request details
        welcome_resp = handle_welcome_message()
        details_resp = request_user_details()
        
        # Combine responses
        final_resp = MessagingResponse()
        for msg in welcome_resp.messages:
            final_resp.append(msg)
        for msg in details_resp.messages:
            final_resp.append(msg)
        return final_resp
    
    # Handle other message types
    if is_gym_log(message_body):
        # Handle workout logging
        response = MessagingResponse()
        msg = response.message()
        msg.body("Logging your workout...")
        return response
    
    # Default response
    response = MessagingResponse()
    msg = response.message()
    msg.body("I didn't understand that. Try sending a workout log or type 'help' for options.")
    return response

def is_hello_message(message: str) -> bool:
    """
    Check if message is a greeting
    """
    greetings = {'hello', 'hi', 'hey', 'start', 'help'}
    return message.lower().strip() in greetings