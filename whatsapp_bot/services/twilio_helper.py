import os
from dotenv import load_dotenv
from twilio.rest import Client
from ..dao.raw_message_dao import RawMessageDAO
load_dotenv()

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
twilio_whatsapp_number = 'whatsapp:+14155238886'
class TwilioClient:
    def __init__(self):
        self.client = Client(account_sid, auth_token)

    def get_client(self):
        return self.client

    def get_templates(self):
        return self.client.conversations

    def send_message(self, to: str, message: str):
        RawMessageDAO.create_raw_message(phone_number=to, message=message, incoming=False)
        self.client.messages.create(to=to, from_=twilio_whatsapp_number, body=message)

    def send_template_message(self, to: str, content_sid: str, content_variables: dict = None):
        RawMessageDAO.create_raw_message(phone_number=to, message=f"template:{content_sid}", incoming=False)
        self.client.messages.create(to='whatsapp:'+to, from_=twilio_whatsapp_number, content_sid=content_sid, content_variables=content_variables)

twilio_client = TwilioClient()

