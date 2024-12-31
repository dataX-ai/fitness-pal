import os
from dotenv import load_dotenv
from twilio.rest import Client
from ..dao.raw_message_dao import RawMessageDAO
from ..models import WhatsAppUser
from ..utils.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
load_dotenv()



class TwilioClient:
    def __init__(self):
        self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    def get_client(self):
        return self.client

    def get_templates(self):
        return self.client.conversations

    def send_message(self, user: WhatsAppUser, message: str):
        RawMessageDAO.create_raw_message(user=user, message=message, incoming=False)
        self.client.messages.create(to=user.phone_number, from_=TWILIO_WHATSAPP_NUMBER, body=message)

    def send_template_message(self, user: WhatsAppUser, content_sid: str, content_variables: dict = None):
        RawMessageDAO.create_raw_message(user=user, message=f"template:{content_sid}", incoming=False)
        self.client.messages.create(to='whatsapp:'+user.phone_number, from_=TWILIO_WHATSAPP_NUMBER, content_sid=content_sid, content_variables=content_variables)

twilio_client = TwilioClient()

