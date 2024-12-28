import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from twilio.twiml.messaging_response import MessagingResponse
from .dao.user_dao import UserDAO
from .services.message_handler import handle_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def webhook(request):
    logger.info("=== WEBHOOK ENDPOINT HIT ===")

    try:
        # Get form data
        form_data = {
            "body": request.POST.get('Body'),
            "from": request.POST.get('From'),
            "num_media": request.POST.get('NumMedia', "0"),
            "media_url": request.POST.get('MediaUrl0'),
            "media_type": request.POST.get('MediaContentType0'),
            "message_sid": request.POST.get('MessageSid')
        }
        logger.info(f"Received form data: {json.dumps(form_data, indent=2)}")

        # Get or create user
        phone_number = form_data['from']
        user, created = UserDAO.get_or_create_user(phone_number)

        resp = handle_message(form_data, user)


        return HttpResponse(str(resp), content_type='application/xml')
    
    except Exception as e:
        logger.error(f"ERROR in webhook: {str(e)}")
        logger.error(f"Request data: {request.POST}")
        raise
