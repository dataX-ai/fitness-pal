from typing import Optional
from ..models import PaymentHistory, WhatsAppUser
from ..services import logger_service

logger = logger_service.get_logger()

class PaymentDAO:
    @staticmethod
    def create_payment_record(user: WhatsAppUser, payment_data: dict) -> PaymentHistory:
        """
        Create a new payment history record
        Args:
            user: WhatsAppUser instance
            payment_data: Payment data from Dodo webhook
        """
        try:
            payment_record = PaymentHistory.objects.create(
                user=user,
                subscription_id=payment_data.get('subscription_id'),
                customer_id=payment_data.get('customer', {}).get('customer_id'),
                product_id=payment_data.get('product_id'),
                business_id=payment_data.get('business_id'),
                type=payment_data.get('type'),
                amount=payment_data.get('recurring_pre_tax_amount', 0) / 100,
                currency=payment_data.get('currency', 'USD'),
                status=payment_data.get('status'),
                payment_time=payment_data.get('created_at'),
                next_billing_date=payment_data.get('next_billing_date'),
                trial_period_days=payment_data.get('trial_period_days', 0),
                quantity=payment_data.get('quantity', 1),
                subscription_period_interval=payment_data.get('subscription_period_interval', 'Year'),
                payment_frequency_interval=payment_data.get('payment_frequency_interval', 'Month'),
                subscription_period_count=payment_data.get('subscription_period_count', 1),
                payment_frequency_count=payment_data.get('payment_frequency_count', 1),
                metadata=payment_data.get('metadata', {}),
            )
            return payment_record
        except Exception as e:
            logger.error(f"Error creating payment record: {str(e)}")
            raise

    @staticmethod
    def get_user_payments(user: WhatsAppUser, limit: int = 10) -> list[PaymentHistory]:
        """Get user's payment history"""
        return list(PaymentHistory.objects.filter(user=user).order_by('-created_at')[:limit])

    @staticmethod
    def get_payment_by_subscription_id(subscription_id: str) -> Optional[PaymentHistory]:
        """Get payment record by subscription ID"""
        try:
            return PaymentHistory.objects.get(subscription_id=subscription_id)
        except PaymentHistory.DoesNotExist:
            return None 