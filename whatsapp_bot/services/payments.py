import os
from typing import Dict, Any
from dodopayments import DodoPayments
from django.conf import settings
from .config import ENVIRONMENT, get_product_ids

class PaymentService:
    def __init__(self):
        bearer_token = os.getenv('DODO_PAYMENTS_API_KEY')
        
        self.client = DodoPayments(
            bearer_token=bearer_token,
            environment=ENVIRONMENT
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

        payment = self.client.payments.create({
            'billing': {
                'city': 'NA',
                'country': 'US',
                'state': 'NA',
                'street': 'NA',
                'zipcode': 12345
            },
            'customer': {
                'name': phone,  # Using phone number as the customer name
            },
            'product_cart': [{
                'product_id': product_id,
                'quantity': 1
            }],
            'payment_link': True,
            'return_url': f"{os.getenv('FRONTEND_URL')}/payment/email-confirmation",
            'metadata': {
                'source': 'web_checkout'
            },
        })

        return {
            'client_secret': payment.client_secret,
            'payment_link': payment.payment_link,
            'payment_id': payment.payment_id
        } 