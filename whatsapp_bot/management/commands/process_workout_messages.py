from django.core.management.base import BaseCommand
from ...cron_services.process_pending_workout_messages import process_pending_workout_messages

class Command(BaseCommand):
    help = 'Manually process pending workout messages'

    def handle(self, *args, **options):
        self.stdout.write('Starting to process workout messages...')
        try:
            result = process_pending_workout_messages()
            self.stdout.write(self.style.SUCCESS(f'Successfully completed. {result}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing messages: {str(e)}')) 