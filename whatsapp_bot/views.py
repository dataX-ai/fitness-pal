import json
import logging
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .dao.user_dao import UserDAO
from .services.message_handler import handle_message
from .services.payments import PaymentService
from .utils.jwt_utils import verify_token
from .models import PaymentHistory
from .dao.user_dao import UserDAO
from .services import logger_service
from .utils.formatUtils import format_phone_number
from standardwebhooks import Webhook
from .utils.config import DODO_WEBHOOK_SECRET
from .services.payments import handle_dodo_webhook
from django.db import connection
from .models import WhatsAppUser, BodyHistory, WorkoutSession, ProgressPhoto
from .services.dashboard_services import get_dashboard_user_data
import pandas as pd
import os
from .utils.config import EXERCISE_LIST_DF

# Configure logging
logger = logger_service.get_logger()


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
        logger.debug(f"Received form data: {json.dumps(form_data, indent=2)}")

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
@require_http_methods(["POST", "OPTIONS"])
def create_payment(request):
    if request.method == "OPTIONS":
        response = HttpResponse()
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
        
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
                return JsonResponse({'error': 'Phone number not found in token'}, status=401)
        except ValueError as ve:
            logger.error(f"Token verification failed: {str(ve)}")
            return JsonResponse({'error': str(ve)}, status=401)
            
        # Parse JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
        
        # Validate amount
        if not data.get('amount'):
            return JsonResponse({'error': 'Amount is required'}, status=400)
        
        # Add verified phone to data
        data['phone'] = phone
        
        # Initialize payment service and create link
        payment_service = PaymentService()
        result = payment_service.create_payment_link(data)
        
        return JsonResponse(result)
        
    except ValueError as ve:
        logger.error(f"Validation error in create_payment: {str(ve)}")
        return JsonResponse({'error': str(ve)}, status=400)
    except Exception as e:
        logger.error(f"Error in create_payment: {str(e)}")
        logger.exception("Full traceback:")  # This will log the full stack trace
        return JsonResponse(
            {'error': 'Payment creation failed'}, 
            status=500
        )


@csrf_exempt
@require_http_methods(["POST"])
def dodo_webhook(request):
    logger.info("=== DODO WEBHOOK HIT ===")
    return handle_dodo_webhook(request)


@csrf_exempt
def health_check(request):
    """Health check endpoint for Docker"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({"status": "healthy"})
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def fetch_workout_info(request):
    try:
        df = EXERCISE_LIST_DF
        
        # Initialize list to store exercise objects
        exercises = []
        
        # Iterate through DataFrame rows
        for index, row in df.iterrows():            
            # Create exercise object
            exercise = {
                'id': index + 1,
                'name': row['exercise_name'] if pd.notna(row['exercise_name']) else "",
                'gifUrl': row['exercise_image_url'] if pd.notna(row['exercise_image_url']) else "",
                'targetMuscleImage': row['muscles_worked_image'] if pd.notna(row['muscles_worked_image']) else "",
                'targetMuscle': row['muscle_group'] if 'muscle_group' in row and pd.notna(row['muscle_group']) else "",
                'description': row['commentary'] if pd.notna(row['commentary']) else "",
                'category': 'Strength',
                'equipment': 'Body Weight'
            }
            
            exercises.append(exercise)
        
        return JsonResponse({'exercises': exercises}, safe=False)
        
    except Exception as e:
        logger.error(f"Error in fetch_workout_info: {str(e)}")
        return JsonResponse(
            {'error': 'Failed to fetch workout information'}, 
            status=500
        )    

@csrf_exempt
@require_http_methods(["POST"])
def get_user_dashboard_info(request):
    try:
        logger.info(f"Request body: {request.body}")
        user_id = request.POST.get('user-id')
        logger.info(f"Request User ID: {user_id}")
        if not user_id:
            return JsonResponse({'error': 'user-id parameter is required'}, status=400)

        dashboard_data = get_dashboard_user_data(user_id)
        
        if dashboard_data is None:
            return JsonResponse({'error': 'User not found'}, status=404)

        return JsonResponse(dashboard_data)

    except Exception as e:
        logger.error(f"Error in get_user_dashboard_info: {str(e)}")
        return JsonResponse(
            {'error': 'Failed to fetch user dashboard information'},
            status=500
        )


