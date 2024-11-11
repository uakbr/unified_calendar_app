from typing import Dict, Optional, List, Callable
from datetime import datetime, timedelta
import logging
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from calendar_parser import Event
from config import NotificationSettings

logger = logging.getLogger(__name__)

class NotificationManager:
    """Manages event notifications and scheduling."""
    
    def __init__(self, settings: NotificationSettings):
        self.settings = settings
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self._notification_callbacks: List[Callable[[str, Event], None]] = []
        self._scheduled_jobs: Dict[str, str] = {}  # event_id: job_id
    
    def add_notification_callback(self, callback: Callable[[str, Event], None]) -> None:
        """Add callback to be called when notification triggers."""
        self._notification_callbacks.append(callback)
    
    def schedule_notification(self, event: Event) -> None:
        """Schedule notification for an event."""
        if not self.settings.enabled:
            return
            
        # Remove any existing notification for this event
        self.remove_notification(event.id)
        
        # Calculate notification time
        notification_time = self._calculate_notification_time(event)
        if not notification_time:
            return
            
        try:
            # Schedule the notification
            job = self.scheduler.add_job(
                func=self._trigger_notification,
                trigger=DateTrigger(run_date=notification_time, timezone=pytz.UTC),
                args=[event],
                id=f"notification_{event.id}"
            )
            self._scheduled_jobs[event.id] = job.id
            logger.info(f"Scheduled notification for event {event.id} at {notification_time}")
        except Exception as e:
            logger.error(f"Failed to schedule notification for event {event.id}: {str(e)}")
    
    def remove_notification(self, event_id: str) -> None:
        """Remove scheduled notification for an event."""
        job_id = self._scheduled_jobs.get(event_id)
        if job_id:
            try:
                self.scheduler.remove_job(job_id)
                del self._scheduled_jobs[event_id]
                logger.info(f"Removed notification for event {event_id}")
            except Exception as e:
                logger.error(f"Failed to remove notification for event {event_id}: {str(e)}")
    
    def update_settings(self, settings: NotificationSettings) -> None:
        """Update notification settings and reschedule if needed."""
        old_enabled = self.settings.enabled
        self.settings = settings
        
        # If notifications were disabled and are now enabled, or vice versa
        if old_enabled != settings.enabled:
            self._reschedule_all_notifications()
    
    def _calculate_notification_time(self, event: Event) -> Optional[datetime]:
        """Calculate when notification should trigger for an event."""
        now = datetime.now(pytz.UTC)
        
        # Get notification time delta (custom or default)
        time_before = self.settings.custom_times.get(
            event.id,
            self.settings.default_time
        )
        
        notification_time = event.start_time - time_before
        
        # Don't schedule if notification time has passed
        if notification_time <= now:
            return None
            
        return notification_time
    
    def _trigger_notification(self, event: Event) -> None:
        """Trigger notification callbacks for an event."""
        try:
            message = self._format_notification_message(event)
            for callback in self._notification_callbacks:
                try:
                    callback(message, event)
                except Exception as e:
                    logger.error(f"Notification callback failed: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to trigger notification: {str(e)}")
        finally:
            # Clean up the job reference
            self._scheduled_jobs.pop(event.id, None)
    
    def _format_notification_message(self, event: Event) -> str:
        """Format notification message for an event."""
        if event.location:
            return f"Upcoming: {event.title} at {event.location}"
        return f"Upcoming: {event.title}"
    
    def _reschedule_all_notifications(self) -> None:
        """Reschedule all notifications (used when settings change)."""
        # Store current jobs to reschedule
        current_events = [
            job.args[0] for job in self.scheduler.get_jobs()
            if job.id in self._scheduled_jobs.values()
        ]
        
        # Clear current schedule
        self.scheduler.remove_all_jobs()
        self._scheduled_jobs.clear()
        
        # Reschedule if enabled
        if self.settings.enabled:
            for event in current_events:
                self.schedule_notification(event)

    def shutdown(self) -> None:
        """Shutdown the notification scheduler."""
        self.scheduler.shutdown()