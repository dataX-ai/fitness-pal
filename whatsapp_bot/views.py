import json
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .dao.user_dao import UserDAO
from .services.message_handler import handle_message
from .services.payments import PaymentService
from .utils.jwt_utils import verify_token

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


@csrf_exempt
@require_http_methods(["POST"])
def create_payment(request):
    logger.info("=== PAYMENT ENDPOINT HIT ===")
    
    try:
        # Check authorization
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        # Extract and verify token
        token = auth_header.split(' ')[1]
        try:
            decoded = verify_token(token)
            phone = decoded.get('Phone')
            if not phone:
                return JsonResponse({'error': 'Invalid token payload'}, status=401)
        except ValueError as ve:
            return JsonResponse({'error': str(ve)}, status=401)
            
        # Parse JSON body
        data = json.loads(request.body)
        
        # Validate amount and ensure phone matches token
        if not data.get('amount'):
            return JsonResponse({'error': 'Amount is required'}, status=400)
        
        # Add verified phone to data
        data['phone'] = phone
        
        # Initialize payment service
        payment_service = PaymentService()
        
        # Create payment link
        result = payment_service.create_payment_link(data)
        
        return JsonResponse(result)
        
    except ValueError as ve:
        logger.error(f"Validation error in create_payment: {str(ve)}")
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        logger.error(f"Error in create_payment: {str(e)}")
        return JsonResponse(
            {'error': 'Payment creation failed'}, 
            status=500
        )
