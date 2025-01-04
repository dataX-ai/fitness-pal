from ..dao.user_dao import UserDAO
from ..models import WhatsAppUser

def is_hello_message(message: str) -> bool:
    """
    Check if message is a greeting
    """
    greetings = {'hello', 'hi', 'hey', 'start', 'help'}
    return message.lower().strip() in greetings