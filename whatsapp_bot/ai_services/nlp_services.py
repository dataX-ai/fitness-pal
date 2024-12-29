from ..services import logger_service
from .nlp_processor import extract_height_weight, classify_message_intent, MessageIntent, extract_name_response

logger = logger_service.get_logger

def is_name_response(message: str) -> tuple[bool, str]:
    """
    Check if message is a name response
    Args:
        message: The message text
    Returns:
        True/False, name
    """
    if classify_message_intent(message) == MessageIntent.NAME:
        try:
            return True, extract_name_response(message)
        except Exception as e:
            logger.error(f"Error in extracting name: {e}")
    return False, None


def is_measurement_response(message: str) -> tuple[bool, float, float]:
    """
    Check if message is a measurement response and extract measurement
    Args:
        message: The message text
    Returns:
        True or False
    """
    # TODO: Implement NLP logic
    classification = classify_message_intent(message)
    if classification == MessageIntent.HEIGHT_WEIGHT:
        try:
            extracted_data = extract_height_weight(message)
            return True, extracted_data['height'], extracted_data['weight']
        except Exception as e:
            logger.error(f"Error in extracting height/weight: {e}")
        return False, None, None


def is_gym_log(message: str) -> bool:
    """
    Determine if the message is a gym log.
    Args:
        message: The user's message text
    Returns:
        True or False
    """
    # TODO: Implement NLP logic
    if classify_message_intent(message) == MessageIntent.EXERCISE:
        return True
    else:
        return False
