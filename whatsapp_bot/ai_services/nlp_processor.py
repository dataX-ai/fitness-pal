from typing import Dict, List, Optional, Tuple
from ..models import WhatsAppUser
def extract_workout_details(message: str) -> Dict[str, any]:
    """
    Extract workout information from user messages.
    Args:
        message: The user's message text
    Returns:
        Dictionary containing extracted workout details
    """
    # TODO: Implement NLP logic
    pass

def is_gym_log(message: str) -> bool:
    """
    Determine if the message is a gym log.
    Args:
        message: The user's message text
    Returns:
        True or False
    """
    # TODO: Implement NLP logic
    pass

def is_name_response(message: str, user: WhatsAppUser) -> tuple[bool, str]:
    """
    Check if message is a name response and extract name
    Args:
        message: The message text
        user: WhatsAppUser object
    """
    # TODO: Implement NLP logic
    return True, "John Doe"
    pass