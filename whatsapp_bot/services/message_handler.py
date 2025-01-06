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
from ..dao.exercise_dao import WorkoutSessionDAO
from ..models import RawMessage
from .subscription_check import SubscriptionCheck

logger = logger_service.get_logger()

###############################################1
# Success Response Messages
###############################################

def handle_name_success(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    message = f"Thanks {user.name}!!"
    add_message_to_response(response, message, user)
    
    if not BodyHistoryDAO.has_activity(user):
        add_body_activity_message(response, user)
    elif not BodyHistoryDAO.has_measurements(user):
        add_height_weight_message(response, user)
    else:
        add_start_track_message(response, user)
    return response

def handle_activity_success(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    latest_metrics = BodyHistoryDAO.get_latest_metrics(user)
    if user.name:
        message = f"Thanks {user.name}! Your activity level has been set to {BodyHistoryDAO.ACTIVITY_CHOICES[latest_metrics.activity]}"
    else:
        message = f"Thanks! Your activity level has been set to {BodyHistoryDAO.ACTIVITY_CHOICES[latest_metrics.activity]}"
    add_message_to_response(response, message, user)
    
    if not user.name:
        add_name_message(response, user)
    elif not BodyHistoryDAO.has_measurements(user):
        add_height_weight_message(response, user)
    else:
        add_start_track_message(response, user)
    return response

def handle_height_weight_success(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    message = "Thanks! Your measurements has been recorded."
    add_message_to_response(response, message, user)
    if not user.name:
        add_name_message(response, user)
    elif not BodyHistoryDAO.has_activity(user):
        add_body_activity_message(response, user)
    elif not BodyHistoryDAO.has_goal(user):
        add_goal_message(response, user)
    else:
        add_start_track_message(response, user)
    return response

def handle_goal_success(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    latest_metrics = BodyHistoryDAO.get_latest_metrics(user)
    goal = latest_metrics.goal if latest_metrics else None
    goal_description = BodyHistoryDAO.GOAL_CHOICES.get(goal, '')

    if user.name:
        message = f"Thanks {user.name}! Your fitness goal has been set to {goal_description}"
    else:
        message = f"Thanks! Your fitness goal has been set to {goal_description}"
    add_message_to_response(response, message, user)
    
    if not user.name:
        add_name_message(response, user)
    elif not BodyHistoryDAO.has_activity(user):
        add_body_activity_message(response, user)
    elif not BodyHistoryDAO.has_measurements(user):
        add_height_weight_message(response, user)
    else:
        add_start_track_message(response, user)
    return response


###############################################
# Retry Response Messages
###############################################

def handle_name_retry(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    add_name_message(response, user)
    return response

def handle_activity_retry(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    add_body_activity_message(response, user)
    return response

def handle_height_weight_retry(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    add_height_weight_message(response, user)
    return response

def handle_height_retry(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    add_only_height_message(response, user)
    return response

def handle_weight_retry(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    add_only_weight_message(response, user)
    return response

def handle_goal_retry(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    add_goal_message(response, user)
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
        add_name_message(response, user)
    elif not BodyHistoryDAO.has_activity(user):
        add_body_activity_message(response, user)
    elif not BodyHistoryDAO.has_measurements(user):
        add_height_weight_message(response, user)
    elif not BodyHistoryDAO.has_goal(user):
        add_goal_message(response, user)

    return response

def handle_name_message(user: WhatsAppUser, message_body: str) -> MessagingResponse:
    is_name, extracted_name = is_name_response(message_body)
    if is_name and extracted_name:
        user = UserDAO.update_user_details(user.phone_number, name=extracted_name)
        if user:
            return handle_name_success(user)
        else:
            return handle_name_retry(user)
    else:
        return handle_name_retry(user)

def handle_activity_message(user: WhatsAppUser, message_body: str) -> MessagingResponse:
    selected_activity = message_body.replace("\n", " ").strip().lower()
    activity_map = {key.strip().lower(): value for key, value in BodyHistoryDAO.ACTIVITY_CHOICES.items()}
    logger.info(f"Activity map: {activity_map}, selected activity: {selected_activity}, message body: {message_body}")
    if selected_activity in activity_map:
        BodyHistoryDAO.create_entry(user, activity=selected_activity)
        return handle_activity_success(user)
    else:
        return handle_activity_retry(user)

def handle_measurement_message(user: WhatsAppUser, message_body: str) -> MessagingResponse:
        result = is_measurement_response(message_body)
        bodyHistory = None
        if result:
            is_measurement, height, weight = result

            if is_measurement:
                if weight and height and 80 <= height <= 250 and 30 <= weight <= 200:
                    bodyHistory = BodyHistoryDAO.create_entry(user, height=height, weight=weight)
                    logger.debug(f"Measurement success: {height}, {weight}")
                    return handle_height_weight_success(user)
                elif height and 80 <= height <= 250:
                    bodyHistory = BodyHistoryDAO.create_entry(user, height=height)
                    logger.debug(f"Measurement success: height: {weight}")
                elif weight and 30 <= weight <= 200:  # Basic validation
                    bodyHistory = BodyHistoryDAO.create_entry(user, weight=weight)
                    logger.debug(f"Measurement success: weight: {weight}")

        if not bodyHistory:
            bodyHistory = BodyHistoryDAO.get_latest_metrics(user)

        height = bodyHistory.height if bodyHistory else None
        weight = bodyHistory.weight if bodyHistory else None

        if not height and not weight:
            return handle_height_weight_retry(user)
        elif not height:
            return handle_height_retry(user)
        elif not weight:
            return handle_weight_retry(user)
        else:
            return handle_height_weight_success(user)

def handle_gym_log_message(user: WhatsAppUser, raw_message: RawMessage) -> MessagingResponse:
    session = WorkoutSessionDAO.get_active_session(user)
    if session:
        WorkoutSessionDAO.add_raw_message(session, raw_message)
    else:
        session = WorkoutSessionDAO.create_session(user)
        WorkoutSessionDAO.add_raw_message(session, raw_message)
    response = MessagingResponse()
    message = "Logging your workout."
    add_message_to_response(response, message, user)
    return response

def handle_goal_message(user: WhatsAppUser, message_body: str) -> MessagingResponse:
    selected_goal = message_body.replace("\n", " ").strip().lower()
    goal_map = {key.strip().lower(): value for key, value in BodyHistoryDAO.GOAL_CHOICES.items()}
    logger.info(f"Goal map: {goal_map}, selected goal: {selected_goal}")
    if selected_goal in goal_map.keys():
        logger.info(f"present in goal map")
        BodyHistoryDAO.create_entry(user, goal=selected_goal)
        return handle_goal_success(user)
    else:
        return handle_goal_retry(user)

def handle_message_limit_exceeded(user: WhatsAppUser) -> MessagingResponse:
    response = MessagingResponse()
    message = f"You've reached your daily message limit. Please try again tomorrow or upgrade to our paid plan for unlimited messages."
    add_message_to_response(response, message, user)
    return response



###############################################
# Main Message Handler
###############################################

def handle_message(form_data: Dict[str, Any], user: WhatsAppUser) -> MessagingResponse:
    """
    Main message handler using Twilio's format
    """
    message_body = form_data.get('body', '')

    # Store raw message
    raw_message = RawMessageDAO.create_raw_message(user=user, message=message_body, incoming=True)

    # If hello message, handle welcome flow
    if not user.name and is_hello_message(message_body):
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
        latest_metrics = BodyHistoryDAO.get_latest_metrics(user)
        logger.debug(f"User already has activity: {latest_metrics.activity if latest_metrics else None}")

    # If no measurements, check if this is height/weight input
    if not BodyHistoryDAO.has_measurements(user):
        return handle_measurement_message(user, message_body)
    else:
        latest_metrics = BodyHistoryDAO.get_latest_metrics(user)
        logger.debug(f"User already has measurements: {latest_metrics.height if latest_metrics else None} {latest_metrics.weight if latest_metrics else None}")

    # If no goal, check if this is a goal selection
    if not BodyHistoryDAO.has_goal(user):
        return handle_goal_message(user, message_body)
    else:
        latest_metrics = BodyHistoryDAO.get_latest_metrics(user)
        logger.debug(f"User already has goal: {latest_metrics.goal if latest_metrics else None}")

    # Check if user can send more messages
    if not user.paid and not SubscriptionCheck.can_send_message(user):
        return handle_message_limit_exceeded(user)

    if is_hello_message(message_body):
        return handle_welcome_and_details(user)

    # Handle other message types
    if is_gym_log(message_body):
        return handle_gym_log_message(user, raw_message)

    # Default response
    response = MessagingResponse()
    message = "I didn't understand that. Try sending a workout log or type 'help' for options."
    add_message_to_response(response, message, user)
    return response

