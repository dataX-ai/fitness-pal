import os
from typing import Dict, Any
from dodopayments import DodoPayments
from ..utils.config import DODO_ENVIRONMENT, get_product_ids, WHATSAPP_PAYMENT_SUCCESS_TEMPLATE_SID, WHATSAPP_PAYMENT_FAILED_TEMPLATE_SID, DODO_SUBSCRIPTION_NAMES
from ..services import logger_service
from django.http import JsonResponse, HttpResponseForbidden
from ..models import PaymentHistory
from ..dao.user_dao import UserDAO
from ..utils.formatUtils import format_phone_number
from standardwebhooks import Webhook
from ..utils.config import DODO_WEBHOOK_SECRET
from ..dao.payment_dao import PaymentDAO
from .twilio_services import twilio_client
import json

logger = logger_service.get_logger()

class PaymentService:
    def __init__(self):
        bearer_token = os.getenv('DODO_PAYMENTS_API_KEY')
        
        self.client = DodoPayments(
            bearer_token=bearer_token,
            environment=DODO_ENVIRONMENT
        )
        
        # Get product IDs from config
        self.DODO_PRODUCT_IDS = get_product_ids()

    def create_payment_link(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a payment link using DodoPayments SDK"""

        amount = str(data.get('amount'))
        phone = data.get('phone')
        
        if not phone:
            raise ValueError('Phone number is required')

        product_id = self.DODO_PRODUCT_IDS.get(amount)
        if not product_id:
            raise ValueError('Invalid amount')

        # Create payment using the SDK with unpacked arguments
        payment = self.client.subscriptions.create(
            billing={
                "city": "NA",
                "country": "US",
                "state": "NA",
                "street": "NA",
                "zipcode": 12345,
            },
            customer={
                "name": phone,  # Using phone as customer_id
                "email": "test@test.com",
            },
            product_id=product_id,
            quantity=1,
            payment_link=True,
            return_url=f"{os.getenv('FRONTEND_URL')}/payment/email-confirmation",
            metadata={
                'source': 'web_checkout'
            }
        )

        return {
            'clientSecret': payment.client_secret,
            'paymentLink': payment.payment_link,
            'subscriptionId': payment.subscription_id
        }


def handle_dodo_webhook(request):
    try:
        # Get webhook secret
        webhook_secret = DODO_WEBHOOK_SECRET
        if not webhook_secret:
            logger.error("Webhook secret not configured")
            return HttpResponseForbidden('No webhook secret configured')

        # Get raw body and convert headers to dict
        raw_body = request.body.decode('utf-8')
        headers = dict(request.headers)  # Convert HttpHeaders to dict directly

        # Initialize webhook and verify
        wh = Webhook(webhook_secret)
        wh.verify(raw_body, headers)

        # Parse the body after verification
        body = json.loads(raw_body)
        payment_data = body.get('data', {})
        payment_data['type'] = body.get('type')
        payment_data['business_id'] = body.get('business_id')

        # Extract payment data
        type = payment_data.get('type')
        subscription_id = payment_data.get('subscription_id')
        business_id = payment_data.get('business_id')
        total_amount = payment_data.get('recurring_pre_tax_amount', 0)  # This is in cents
        amount_in_dollars = str(total_amount / 100)  # Convert to dollars and string
        customer = payment_data.get('customer', {})
        created_at = payment_data.get('created_at')
        status = payment_data.get('status')

        # Extract and format phone number from customer name
        phone_number = format_phone_number(customer.get('name'))
        if not phone_number:
            logger.error("No phone number found in webhook data")
            return JsonResponse({'error': 'No phone number found'}, status=400)

        # Get or create user
        user = UserDAO.get_or_create_user(phone_number)

        # Create payment history record using DAO
        payment_record = PaymentDAO.create_payment_record(user, payment_data)

        # Update user paid status if payment successful
        if type == 'subscription.active' and status == 'active':
            UserDAO.update_paid_status(user, True)
            logger.info(f"Updated paid status for user {phone_number}")
            template_data = {
                "1": DODO_SUBSCRIPTION_NAMES.get(amount_in_dollars, "Subscription"),
                "2": subscription_id
            }
            twilio_client.send_template_message(
                phone_number, 
                WHATSAPP_PAYMENT_SUCCESS_TEMPLATE_SID, 
                json.dumps(template_data)
            )
        elif type == 'subscription.inactive' and status == 'inactive':
            UserDAO.update_paid_status(user, False)
            template_data = {
                "1": DODO_SUBSCRIPTION_NAMES.get(amount_in_dollars, "Subscription"),
                "2": subscription_id
            }
            twilio_client.send_template_message(
                phone_number, 
                WHATSAPP_PAYMENT_FAILED_TEMPLATE_SID, 
                json.dumps(template_data)
            )

        return JsonResponse({'status': '200'})

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        logger.exception("Full traceback:")
        return JsonResponse({'error': 'Webhook processing failed'}, status=500)

