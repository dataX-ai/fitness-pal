import os
from dotenv import load_dotenv
from twilio.rest import Client
from ..dao.raw_message_dao import RawMessageDAO
from ..utils.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
load_dotenv()



class TwilioClient:
    def __init__(self):
        self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    def get_client(self):
        return self.client

    def get_templates(self):
        return self.client.conversations

    def send_message(self, to: str, message: str):
        RawMessageDAO.create_raw_message(phone_number=to, message=message, incoming=False)
        self.client.messages.create(to=to, from_=TWILIO_WHATSAPP_NUMBER, body=message)

    def send_template_message(self, to: str, content_sid: str, content_variables: dict = None):
        RawMessageDAO.create_raw_message(phone_number=to, message=f"template:{content_sid}", incoming=False)
        self.client.messages.create(to='whatsapp:'+to, from_=TWILIO_WHATSAPP_NUMBER, content_sid=content_sid, content_variables=content_variables)

twilio_client = TwilioClient()

