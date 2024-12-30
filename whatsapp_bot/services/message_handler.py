from typing import Dict, Any
from twilio.twiml.messaging_response import MessagingResponse
from ..models import WhatsAppUser
from ..dao.raw_message_dao import RawMessageDAO
from ..dao.user_dao import UserDAO
from ..dao.body_history_dao import BodyHistoryDAO
from .message_flow import is_hello_message
from ..ai_services.nlp_services import is_name_response, is_measurement_response, is_gym_log
from .message_types import *
from .twilio_services import twilio_client
from ..services import logger_service
from ..dao.workout_session_dao import WorkoutSessionDAO
from ..models import RawMessage
logger = logger_service.get_logger()

###############################################1
# Success Response Messages
###############################################

def handle_name_success(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    message = f"Thanks {user.name}!!"
    add_message_to_response(response, message, user)
    
    if not BodyHistoryDAO.has_activity(user):
        add_body_history_message(response, user)
    elif not BodyHistoryDAO.has_measurements(user):
        add_height_weight_message(response)
    else:
        add_start_track_message(response, user)
    return response

def handle_activity_success(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    if user.name:
        message = f"Thanks {user.name}! Your activity level has been set to {BodyHistoryDAO.ACTIVITY_CHOICES[BodyHistoryDAO.get_latest_metrics(user).get('activity')]}"
    else:
        message = f"Thanks! Your activity level has been set to {BodyHistoryDAO.ACTIVITY_CHOICES[BodyHistoryDAO.get_latest_metrics(user).get('activity')]}"
    add_message_to_response(response, message, user)
    
    if not user.name:
        add_name_message(response)
    elif not BodyHistoryDAO.has_measurements(user):
        add_height_weight_message(response)
    else:
        add_start_track_message(response, user)
    return response

def handle_height_weight_success(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    if not user.name:
        add_name_message(response)
    elif not BodyHistoryDAO.has_activity(user):
        add_body_history_message(response, user)
    else:
        message = "Thanks! Your measurements has been recorded."
        add_message_to_response(response, message, user)
    return response


###############################################
# Retry Response Messages
###############################################

def handle_name_retry(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    add_name_message(response)
    return response

def handle_activity_retry(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    add_body_history_message(response, user)
    return response

def handle_height_weight_retry(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    add_height_weight_message(response)
    return response

def handle_height_retry(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    add_only_height_message(response)
    return response

def handle_weight_retry(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    add_only_weight_message(response)
    return response

###############################################
# Handle Incoming Messages
###############################################

def handle_welcome_and_details(user: WhatsAppUser) -> MessagingResponse:
    """
    Generate combined welcome and details request based on user state
    """
    response = MessagingResponse()

    # First message - Welcome
    message ="""Hello! Welcome to GymTracker! 💪

Track your workouts in natural language, monitor progress, and achieve your fitness goals."""
    add_message_to_response(response, message, user)
    # Second message - Based on user state
    if not user.name:
        add_name_message(response)
    elif not BodyHistoryDAO.has_activity(user):
        add_body_history_message(response, user)
    elif not BodyHistoryDAO.has_measurements(user):
        add_height_weight_message(response)

    return response

def handle_name_message(user: WhatsAppUser, message_body: str) -> MessagingResponse:
    is_name, extracted_name = is_name_response(message_body, user)
    if is_name and extracted_name:
        UserDAO.update_user_details(user.phone_number, name=extracted_name)
        return handle_name_success(user)
    else:
        return handle_name_retry(user)

def handle_activity_message(user: WhatsAppUser, message_body: str) -> MessagingResponse:
    selected_activity = message_body.replace("\n", " ").strip().lower()
    activity_map = {value.strip().lower(): key for key, value in BodyHistoryDAO.ACTIVITY_CHOICES}
    if selected_activity in activity_map:
        BodyHistoryDAO.create_entry(user, activity=activity_map[selected_activity])
        return handle_activity_success(user)
    else:
        return handle_activity_retry(user)

def handle_measurement_message(user: WhatsAppUser, message_body: str) -> MessagingResponse:
        is_measurement, height, weight = is_measurement_response(message_body)
        if is_measurement:
            if weight and height and 80 <= height <= 250 and 30 <= weight <= 200:
                BodyHistoryDAO.create_entry(user, height=height, weight=weight)
                return handle_height_weight_success(user)
            elif height and 80 <= height <= 250:
                bodyHistory = BodyHistoryDAO.create_entry(user, height=height)
                if bodyHistory.weight:
                    return handle_height_weight_success(user)
                else:
                    return handle_height_weight_retry(user)
            elif weight and 30 <= weight <= 200:  # Basic validation
                bodyHistory = BodyHistoryDAO.create_entry(user, weight=weight)
                if bodyHistory.height:
                    return handle_height_weight_success(user)
                else:
                    return handle_height_weight_retry(user)
        else:
            return handle_height_weight_retry(user)

def handle_gym_log_message(user: WhatsAppUser, raw_message: RawMessage) -> MessagingResponse:
    if WorkoutSessionDAO.get_active_session(user.phone_number):
        WorkoutSessionDAO.add_raw_message(session, raw_message)
    else:
        session = WorkoutSessionDAO.create_session(user)
        WorkoutSessionDAO.add_raw_message(session, raw_message)
    response = MessagingResponse()
    message = "Logging your workout."
    add_message_to_response(response, raw_message.message, user)
    return response

###############################################
# Main Message Handler
###############################################

def handle_message(form_data: Dict[str, Any], user: WhatsAppUser) -> MessagingResponse:
    """
    Main message handler using Twilio's format
    """
    phone_number = form_data.get('from')
    message_body = form_data.get('body', '')

    # Store raw message
    raw_message = RawMessageDAO.create_raw_message(phone_number, message_body, True)

    # If hello message, handle welcome flow
    if is_hello_message(message_body):
        return handle_welcome_and_details(user)

    # If no name, check if this is a name response
    if not user.name:
        return handle_name_message(user, message_body)
    else:
        logger.debug(f"User already has name: {user.name}")

    # If no activity, check if this is an activity selection
    if not BodyHistoryDAO.has_activity(user):
        return handle_activity_message(user, message_body)
    else:
        logger.debug(f"User already has activity: {BodyHistoryDAO.get_latest_metrics(user).get('activity')}")

    # If no measurements, check if this is height/weight input
    if not BodyHistoryDAO.has_measurements(user):
        return handle_measurement_message(user, message_body)
    else:
        logger.debug(f"User already has measurements: {BodyHistoryDAO.get_latest_metrics(user).get('height')} {BodyHistoryDAO.get_latest_metrics(user).get('weight')}")

    # Handle other message types
    if is_gym_log(message_body):
        return handle_gym_log_message(user, response, raw_message)
    
    # Default response
    response = MessagingResponse()
    message = "I didn't understand that. Try sending a workout log or type 'help' for options."
    add_message_to_response(response, message, user)
    return response

