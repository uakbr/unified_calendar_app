import unittest
from datetime import datetime, timedelta
import pytz
from unittest.mock import Mock, patch, MagicMock
import platform
from notification_manager import NotificationManager, NotificationPriority
from calendar_parser import Event
from config import NotificationSettings

class TestNotificationManager(unittest.TestCase):
    def setUp(self):
        """Setup test environment before each test."""
        self.settings = NotificationSettings(
            default_time=timedelta(minutes=10),
            enabled=True,
            sound_enabled=True,
            custom_times={"test_event": timedelta(minutes=5)}
        )
        self.manager = NotificationManager(self.settings)
        self.now = datetime.now(pytz.UTC)
        
        # Create sample events
        self.test_event = Event(
            id="test1",
            title="Test Event",
            start_time=self.now + timedelta(minutes=30),
            end_time=self.now + timedelta(minutes=90),
            calendar_source="test_source"
        )
        
        self.all_day_event = Event(
            id="test2",
            title="All Day Event",
            start_time=self.now.replace(hour=0, minute=0, second=0),
            end_time=(self.now + timedelta(days=1)).replace(hour=0, minute=0, second=0),
            calendar_source="test_source",
            is_all_day=True
        )

    def tearDown(self):
        """Clean up after each test."""
        self.manager.shutdown()

    def test_notification_scheduling_priority(self):
        """Test notification scheduling with different priority levels."""
        # Test high priority
        self.manager.schedule_notification(self.test_event, NotificationPriority.HIGH)
        jobs = self.manager.scheduler.get_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].args[1], NotificationPriority.HIGH)
        
        # Test low priority
        self.manager.remove_notification(self.test_event.id)
        self.manager.schedule_notification(self.test_event, NotificationPriority.LOW)
        jobs = self.manager.scheduler.get_jobs()
        self.assertEqual(jobs[0].args[1], NotificationPriority.LOW)

    @patch('notification_manager.winsound.PlaySound' if platform.system() == 'Windows' else 'os.system')
    def test_notification_sound_by_priority(self, mock_sound):
        """Test sound behavior for different priority levels."""
        # High priority should play sound
        self.manager._trigger_notification(
            self.test_event,
            NotificationPriority.HIGH,
            self.now
        )
        mock_sound.assert_called_once()
        mock_sound.reset_mock()
        
        # Low priority should not play sound
        self.manager._trigger_notification(
            self.test_event,
            NotificationPriority.LOW,
            self.now
        )
        mock_sound.assert_not_called()

    def test_settings_update(self):
        """Test notification behavior when settings change."""
        # Schedule initial notification
        self.manager.schedule_notification(self.test_event)
        self.assertEqual(len(self.manager.scheduler.get_jobs()), 1)
        
        # Disable notifications
        new_settings = NotificationSettings(
            default_time=timedelta(minutes=10),
            enabled=False,
            sound_enabled=True
        )
        self.manager.update_settings(new_settings)
        self.assertEqual(len(self.manager.scheduler.get_jobs()), 0)
        
        # Re-enable with different default time
        new_settings.enabled = True
        new_settings.default_time = timedelta(minutes=15)
        self.manager.update_settings(new_settings)
        jobs = self.manager.scheduler.get_jobs()
        self.assertEqual(len(jobs), 1)

    def test_custom_notification_times(self):
        """Test custom notification times for specific events."""
        # Event with custom time
        custom_event = Event(
            id="test_event",  # Matches custom_times in settings
            title="Custom Time Event",
            start_time=self.now + timedelta(hours=1),
            end_time=self.now + timedelta(hours=2),
            calendar_source="test_source"
        )
        
        self.manager.schedule_notification(custom_event)
        jobs = self.manager.scheduler.get_jobs()
        self.assertEqual(len(jobs), 1)
        
        # Verify custom time was used
        expected_time = custom_event.start_time - timedelta(minutes=5)
        job_time = jobs[0].trigger.run_date
        self.assertEqual(job_time.replace(tzinfo=pytz.UTC), expected_time)

    def test_multiple_notifications(self):
        """Test handling multiple notifications for the same event."""
        self.settings.custom_times[self.test_event.id] = timedelta(minutes=5)
        self.manager.schedule_notification(self.test_event)
        
        jobs = self.manager.scheduler.get_jobs()
        self.assertEqual(len(jobs), 2)  # Default (10min) and custom (5min)
        
        # Verify job times
        times = sorted(job.trigger.run_date.replace(tzinfo=pytz.UTC) 
                      for job in jobs)
        expected_times = sorted([
            self.test_event.start_time - timedelta(minutes=5),
            self.test_event.start_time - timedelta(minutes=10)
        ])
        self.assertEqual(times, expected_times)

    def test_notification_callbacks(self):
        """Test notification callback system with multiple callbacks."""
        callback_data = []
        error_callback = Mock(side_effect=Exception("Test error"))
        
        def test_callback(message, event, priority):
            callback_data.append((message, event, priority))
        
        # Add both callbacks
        self.manager.add_notification_callback(test_callback)
        self.manager.add_notification_callback(error_callback)
        
        # Trigger notification
        self.manager._trigger_notification(
            self.test_event,
            NotificationPriority.HIGH,
            self.now
        )
        
        # Verify working callback executed despite error in other callback
        self.assertEqual(len(callback_data), 1)
        self.assertEqual(callback_data[0][1], self.test_event)
        self.assertEqual(callback_data[0][2], NotificationPriority.HIGH)
        error_callback.assert_called_once()

    @patch('platform.system', return_value='Linux')
    @patch('os.system')
    def test_cross_platform_sound(self, mock_system, mock_platform):
        """Test sound notification on non-Windows platforms."""
        self.manager._play_notification_sound()
        mock_system.assert_called_once()
        
        # Test fallback behavior
        mock_system.side_effect = Exception("Sound error")
        self.manager._play_notification_sound()  # Should not raise exception

    def test_message_formatting(self):
        """Test notification message formatting."""
        # Test immediate notification
        message = self.manager._format_notification_message(
            self.test_event,
            self.test_event.start_time
        )
        self.assertTrue(message.startswith("Starting now"))
        
        # Test future notification with location
        event_with_location = Event(
            id="test3",
            title="Located Event",
            start_time=self.now + timedelta(minutes=30),
            end_time=self.now + timedelta(minutes=90),
            location="Test Location",
            calendar_source="test_source"
        )
        message = self.manager._format_notification_message(
            event_with_location,
            self.now
        )
        self.assertIn("Test Location", message)

if __name__ == '__main__':
    unittest.main()