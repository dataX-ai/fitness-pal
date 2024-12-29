from ..models import RawMessage

class RawMessageDAO:
    @staticmethod
    def create_raw_message(phone_number: str, message: str, incoming: bool) -> RawMessage:
        return RawMessage.objects.create(phone_number=phone_number, message=message, incoming=incoming)

