from typing import Dict, Optional, List, Callable, Set
from datetime import datetime, timedelta
import logging
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from calendar_parser import Event
from config import NotificationSettings
import winsound  # for Windows
import os

logger = logging.getLogger(__name__)

class NotificationPriority:
    LOW = 0
    NORMAL = 1
    HIGH = 2

class NotificationManager:
    """Manages event notifications and scheduling."""
    
    def __init__(self, settings: NotificationSettings):
        self.settings = settings
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self._notification_callbacks: List[Callable[[str, Event, int], None]] = []
        self._scheduled_jobs: Dict[str, Set[str]] = {}  # event_id: set of job_ids
        self._sound_file = os.path.join(os.path.dirname(__file__), 'assets', 'notification.wav')
    
    def add_notification_callback(self, callback: Callable[[str, Event, int], None]) -> None:
        """Add callback to be called when notification triggers.
        Callback receives: message, event, and priority level"""
        self._notification_callbacks.append(callback)
    
    def schedule_notification(self, event: Event, priority: int = NotificationPriority.NORMAL) -> None:
        """Schedule notifications for an event with multiple time points."""
        if not self.settings.enabled:
            return
            
        # Remove any existing notifications for this event
        self.remove_notification(event.id)
        
        # Get all notification times for this event
        notification_times = self._calculate_notification_times(event)
        if not notification_times:
            return
            
        self._scheduled_jobs[event.id] = set()
        
        for notification_time in notification_times:
            try:
                # Schedule the notification
                job = self.scheduler.add_job(
                    func=self._trigger_notification,
                    trigger=DateTrigger(run_date=notification_time, timezone=pytz.UTC),
                    args=[event, priority, notification_time],
                    id=f"notification_{event.id}_{notification_time.timestamp()}"
                )
                self._scheduled_jobs[event.id].add(job.id)
                logger.info(f"Scheduled notification for event {event.id} at {notification_time}")
            except Exception as e:
                logger.error(f"Failed to schedule notification for event {event.id}: {str(e)}")
    
    def remove_notification(self, event_id: str) -> None:
        """Remove all scheduled notifications for an event."""
        job_ids = self._scheduled_jobs.get(event_id, set())
        for job_id in job_ids:
            try:
                self.scheduler.remove_job(job_id)
                logger.info(f"Removed notification job {job_id} for event {event_id}")
            except Exception as e:
                logger.error(f"Failed to remove notification job {job_id}: {str(e)}")
        self._scheduled_jobs.pop(event_id, None)
    
    def update_settings(self, settings: NotificationSettings) -> None:
        """Update notification settings and reschedule if needed."""
        old_enabled = self.settings.enabled
        old_sound = self.settings.sound_enabled
        self.settings = settings
        
        # If notifications were disabled/enabled or sound settings changed
        if old_enabled != settings.enabled or old_sound != settings.sound_enabled:
            self._reschedule_all_notifications()
    
    def _calculate_notification_times(self, event: Event) -> List[datetime]:
        """Calculate all notification times for an event."""
        now = datetime.now(pytz.UTC)
        times = []
        
        # Add custom notification times for this event
        custom_times = self.settings.custom_times.get(event.id, [])
        for time_before in custom_times:
            notification_time = event.start_time - time_before
            if notification_time > now:
                times.append(notification_time)
        
        # Add default notification time if no custom times exist
        if not custom_times:
            notification_time = event.start_time - self.settings.default_time
            if notification_time > now:
                times.append(notification_time)
        
        return sorted(times)
    
    def _trigger_notification(self, event: Event, priority: int, scheduled_time: datetime) -> None:
        """Trigger notification callbacks for an event."""
        try:
            message = self._format_notification_message(event, scheduled_time)
            
            # Play sound for normal and high priority notifications if enabled
            if self.settings.sound_enabled and priority >= NotificationPriority.NORMAL:
                self._play_notification_sound()
            
            for callback in self._notification_callbacks:
                try:
                    callback(message, event, priority)
                except Exception as e:
                    logger.error(f"Notification callback failed: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to trigger notification: {str(e)}")
        finally:
            # Remove this specific job ID from tracking
            job_ids = self._scheduled_jobs.get(event.id, set())
            current_job_id = f"notification_{event.id}_{scheduled_time.timestamp()}"
            if current_job_id in job_ids:
                job_ids.remove(current_job_id)
                if not job_ids:  # If no more notifications for this event
                    self._scheduled_jobs.pop(event.id, None)
    
    def _format_notification_message(self, event: Event, scheduled_time: datetime) -> str:
        """Format notification message for an event."""
        time_until = event.start_time - scheduled_time
        if time_until <= timedelta(minutes=1):
            prefix = "Starting now"
        else:
            minutes = int(time_until.total_seconds() / 60)
            prefix = f"In {minutes} minutes"
        
        if event.location:
            return f"{prefix}: {event.title} at {event.location}"
        return f"{prefix}: {event.title}"
    
    def _play_notification_sound(self) -> None:
        """Play notification sound if enabled and file exists."""
        try:
            if os.path.exists(self._sound_file):
                winsound.PlaySound(self._sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception as e:
            logger.error(f"Failed to play notification sound: {str(e)}")
    
    def _reschedule_all_notifications(self) -> None:
        """Reschedule all notifications (used when settings change)."""
        # Store current jobs to reschedule
        current_events = []
        current_priorities = {}
        
        for job in self.scheduler.get_jobs():
            for event_id, job_ids in self._scheduled_jobs.items():
                if job.id in job_ids:
                    event = job.args[0]
                    priority = job.args[1]
                    current_events.append(event)
                    current_priorities[event.id] = priority
                    break
        
        # Clear current schedule
        self.scheduler.remove_all_jobs()
        self._scheduled_jobs.clear()
        
        # Reschedule if enabled
        if self.settings.enabled:
            for event in current_events:
                self.schedule_notification(
                    event,
                    priority=current_priorities.get(event.id, NotificationPriority.NORMAL)
                )

    def shutdown(self) -> None:
        """Shutdown the notification scheduler."""
        self.scheduler.shutdown()