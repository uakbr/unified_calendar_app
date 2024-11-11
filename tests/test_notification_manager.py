import unittest
from datetime import datetime, timedelta
import pytz
from unittest.mock import Mock, patch
from notification_manager import NotificationManager, NotificationPriority
from calendar_parser import Event
from config import NotificationSettings

class TestNotificationManager(unittest.TestCase):
    def setUp(self):
        """Setup test environment before each test."""
        self.settings = NotificationSettings(
            default_time=timedelta(minutes=10),
            enabled=True,
            sound_enabled=True
        )
        self.manager = NotificationManager(self.settings)
        self.now = datetime.now(pytz.UTC)
        
        # Create sample event
        self.test_event = Event(
            id="test1",
            title="Test Event",
            start_time=self.now + timedelta(minutes=30),
            end_time=self.now + timedelta(minutes=90),
            calendar_source="test_source"
        )

    def tearDown(self):
        """Clean up after each test."""
        self.manager.shutdown()

    def test_notification_scheduling(self):
        """Test basic notification scheduling."""
        # Add mock callback
        mock_callback = Mock()
        self.manager.add_notification_callback(mock_callback)
        
        # Schedule notification
        self.manager.schedule_notification(self.test_event)
        
        # Verify job was scheduled
        jobs = self.manager.scheduler.get_jobs()
        self.assertEqual(len(jobs), 1)
        
        # Verify job details
        job = jobs[0]
        self.assertTrue(job.id.startswith(f"notification_{self.test_event.id}"))
        self.assertEqual(job.args[0], self.test_event)
        self.assertEqual(job.args[1], NotificationPriority.NORMAL)

    def test_notification_disabled(self):
        """Test behavior when notifications are disabled."""
        self.settings.enabled = False
        self.manager.schedule_notification(self.test_event)
        
        # Verify no jobs were scheduled
        jobs = self.manager.scheduler.get_jobs()
        self.assertEqual(len(jobs), 0)

    def test_notification_removal(self):
        """Test removing scheduled notifications."""
        self.manager.schedule_notification(self.test_event)
        self.assertEqual(len(self.manager.scheduler.get_jobs()), 1)
        
        self.manager.remove_notification(self.test_event.id)
        self.assertEqual(len(self.manager.scheduler.get_jobs()), 0)

    def test_multiple_notification_times(self):
        """Test scheduling multiple notification times for one event."""
        # Add custom notification time
        self.settings.custom_times[self.test_event.id] = timedelta(minutes=5)
        
        self.manager.schedule_notification(self.test_event)
        jobs = self.manager.scheduler.get_jobs()
        
        # Should have both default (10min) and custom (5min) notifications
        self.assertEqual(len(jobs), 2)

    @patch('notification_manager.winsound.PlaySound')
    def test_notification_sound(self, mock_play_sound):
        """Test notification sound handling."""
        self.settings.sound_enabled = True
        
        # Trigger a notification
        self.manager._trigger_notification(
            self.test_event,
            NotificationPriority.NORMAL,
            self.now
        )
        
        # Verify sound was played
        mock_play_sound.assert_called_once()

    def test_notification_callbacks(self):
        """Test notification callback system."""
        callback_data = []
        
        def test_callback(message, event, priority):
            callback_data.append((message, event, priority))
        
        self.manager.add_notification_callback(test_callback)
        
        # Trigger notification
        self.manager._trigger_notification(
            self.test_event,
            NotificationPriority.HIGH,
            self.now
        )
        
        # Verify callback was called with correct data
        self.assertEqual(len(callback_data), 1)
        message, event, priority = callback_data[0]
        self.assertIn(self.test_event.title, message)
        self.assertEqual(event, self.test_event)
        self.assertEqual(priority, NotificationPriority.HIGH)

    def test_notification_message_formatting(self):
        """Test notification message formatting."""
        # Test immediate notification
        message = self.manager._format_notification_message(
            self.test_event,
            self.test_event.start_time
        )
        self.assertTrue(message.startswith("Starting now"))
        
        # Test future notification
        future_time = self.test_event.start_time - timedelta(minutes=5)
        message = self.manager._format_notification_message(
            self.test_event,
            future_time
        )
        self.assertTrue(message.startswith("In 5 minutes"))

    def test_error_handling(self):
        """Test error handling in notification system."""
        # Add failing callback
        def failing_callback(message, event, priority):
            raise Exception("Test error")
        
        self.manager.add_notification_callback(failing_callback)
        
        # Add working callback
        mock_callback = Mock()
        self.manager.add_notification_callback(mock_callback)
        
        # Trigger notification - should not crash and should call working callback
        self.manager._trigger_notification(
            self.test_event,
            NotificationPriority.NORMAL,
            self.now
        )
        
        mock_callback.assert_called_once()

if __name__ == '__main__':
    unittest.main()