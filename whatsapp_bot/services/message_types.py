from twilio.twiml.messaging_response import MessagingResponse
from ..dao.body_history_dao import BodyHistoryDAO
from ..models import WhatsAppUser
from .twilio_helper import twilio_client
from ..dao.raw_message_dao import RawMessageDAO

def add_message_to_response(response: MessagingResponse, message: str, user: WhatsAppUser):
    RawMessageDAO.create_raw_message(phone_number=user.phone_number, message=message, incoming=False)
    msg = response.message()
    msg.body(message)
    return response

def add_name_message(response: MessagingResponse, user: WhatsAppUser):
    add_message_to_response(response, "Hi, Please provide your name", user)
    return response

def add_body_history_message(response: MessagingResponse, user: WhatsAppUser):
    twilio_client.send_template_message(to=user.phone_number, content_sid="HX924f53aed72555c48b8f5f402a615098")
    return response

def add_height_weight_message(response: MessagingResponse, user: WhatsAppUser):
    message = """Please provide your height and weight:
- Height (in cm)
- Weight (in kg)

Format: "height: 170, weight: 70"
"""
    add_message_to_response(response, message, user)
    return response

def add_only_height_message(response: MessagingResponse, user: WhatsAppUser):
    message ="""Please provide your height:
- Height (in cm)

Format: "height: 170"
"""
    add_message_to_response(response, message, user)
    return response

def add_only_weight_message(response: MessagingResponse, user: WhatsAppUser):
    message = """Please provide your weight:
- Weight (in kg)

Format: "weight: 70"
"""
    add_message_to_response(response, message, user)
    return response

def add_body_composition_message(response: MessagingResponse, user: WhatsAppUser, **kwargs):
    twilio_client.send_template_message(to=user.phone_number, content_sid="HX924f53aed72555c48b8f5f402a615098")
    return response

def add_start_track_message(response: MessagingResponse, user: WhatsAppUser, **kwargs):
    message = f"Thanks {user.name}! Now, let me help you track your fitness journey."
    add_message_to_response(response, message, user)
    return response
