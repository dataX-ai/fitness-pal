from django_cron import CronJobBase, Schedule
from django.utils import timezone
from django_cron.backends.lock.file import FileLock
from django.conf import settings
import os
from .models import WorkoutSession
from .services.logger_service import get_logger
import traceback

logger = get_logger(__name__)

class BaseCronJob(CronJobBase):
    """Base cron job with common best practices"""
    
    # RUN_EVERY_MINS and schedule should be defined in child classes
    
    # Maximum time (in seconds) the job should be allowed to run
    TIMEOUT_SECONDS = 300  # 5 minutes default timeout
    
    # Number of retries if job fails
    MAX_RETRIES = 3
    
    # Allow jobs to run simultaneously?
    ALLOW_PARALLEL_RUNS = False
    
    # Directory for lock files
    LOCK_DIR = os.path.join(settings.BASE_DIR, 'cron_locks')
    
    def __init__(self):
        super().__init__()
        # Ensure lock directory exists
        os.makedirs(self.LOCK_DIR, exist_ok=True)
    
    def do(self):
        """
        Override this method in child class.
        Wrap the actual job execution with error handling and logging.
        """
        raise NotImplementedError("Subclasses must implement do()")
    
    def _acquire_lock(self):
        """Acquire a file-based lock"""
        lock_file = os.path.join(self.LOCK_DIR, f"{self.code}.lock")
        return FileLock(lock_file)
    
    def do_job(self, force=False):
        """Enhanced job execution with best practices"""
        try:
            if not self.ALLOW_PARALLEL_RUNS:
                lock = self._acquire_lock()
                if not lock.acquire():
                    logger.warning(f"Job {self.code} is already running")
                    return
            
            logger.info(f"Starting cron job: {self.code}")
            start_time = timezone.now()
            
            try:
                result = self.do()
                execution_time = (timezone.now() - start_time).total_seconds()
                logger.info(f"Job {self.code} completed successfully in {execution_time} seconds")
                return result
            
            except Exception as e:
                logger.error(f"Error in cron job {self.code}: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
            
        finally:
            if not self.ALLOW_PARALLEL_RUNS:
                lock.release()


class CleanupOldSessionsCronJob(BaseCronJob):
    """
    Cron job to cleanup old workout sessions that are incomplete
    Runs daily at midnight
    """
    RUN_EVERY_MINS = 24 * 60  # once per day
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'whatsapp_bot.cleanup_old_sessions'
    
    TIMEOUT_SECONDS = 600  # 10 minutes timeout for cleanup
    ALLOW_PARALLEL_RUNS = False
    
    def do(self):
        """Cleanup old incomplete workout sessions"""
        try:
            yesterday = timezone.now() - timezone.timedelta(days=1)
            # Use select_for_update() to prevent race conditions
            old_sessions = WorkoutSession.objects.select_for_update().filter(
                created_at__lt=yesterday,
                is_completed=False
            )
            
            count = old_sessions.count()
            if count > 0:
                # Batch delete to handle large datasets efficiently
                batch_size = 1000
                while old_sessions.exists():
                    batch_ids = old_sessions[:batch_size].values_list('id', flat=True)
                    WorkoutSession.objects.filter(id__in=list(batch_ids)).delete()
                    
                logger.info(f"Cleaned up {count} old incomplete workout sessions")
            else:
                logger.info("No old sessions to clean up")
            
            return f"Successfully cleaned up {count} sessions"
            
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise 