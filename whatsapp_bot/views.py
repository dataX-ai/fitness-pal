import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from twilio.twiml.messaging_response import MessagingResponse
from .models import WhatsAppUser, WorkoutSession, Exercise, ProgressPhoto

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def get_welcome_message():
    return """Welcome to FitnessTracker! 🏋️‍♂️

Here's what you can do:
1. Log your workout by describing what you did
2. Get Reports on your workout history
3. Get fitness tips
4. Send a photo of your workout or progress 📸

Just type your workout details and I'll log them for you!
Example: "Did 3 sets of bench press and squats for 1 hour\""""

def process_fitness_activity(message: str, user: WhatsAppUser):
    """
    Process the workout message and create a WorkoutSession with exercises
    """
    # For now, return dummy structured data
    # Later, we'll implement NLP to parse the message
    workout = WorkoutSession.objects.create(
        user=user,
        activity_type="weightlifting",
        duration_minutes=60,
        raw_message=message
    )

    # Create dummy exercises
    Exercise.objects.create(
        workout=workout,
        name="bench press",
        sets=3,
        reps=12
    )
    Exercise.objects.create(
        workout=workout,
        name="squats",
        sets=3,
        reps=12
    )

    return workout

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

        # Create Twilio response object
        resp = MessagingResponse()

        # Get or create user
        phone_number = form_data['from']
        user, created = WhatsAppUser.objects.get_or_create(phone_number=phone_number)
        
        return HttpResponse(str(resp), content_type='application/xml')
    
    except Exception as e:
        logger.error(f"ERROR in webhook: {str(e)}")
        logger.error(f"Request data: {request.POST}")
        raise
