import unittest
from pathlib import Path
import json
from datetime import timedelta
import tempfile
import os
from config import (
    CalendarConfig,
    CalendarSource,
    NotificationSettings,
    DisplaySettings,
    ConfigError,
    ConfigValidationError
)

class TestConfig(unittest.TestCase):
    def setUp(self):
        """Setup test environment before each test."""
        # Create temporary directory for test config files
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
        
        # Sample configuration data
        self.sample_config = {
            'calendar_sources': {
                'source1': {
                    'url': 'http://test1.com/calendar.ics',
                    'color': '#FF0000',
                    'enabled': True,
                    'name': 'Test Calendar 1'
                },
                'source2': {
                    'url': 'http://test2.com/calendar.ics',
                    'color': '#00FF00',
                    'enabled': False,
                    'name': 'Test Calendar 2'
                }
            },
            'notifications': {
                'default_time': 600,  # 10 minutes in seconds
                'enabled': True,
                'sound_enabled': True,
                'custom_times': {
                    'event1': 300,  # 5 minutes in seconds
                    'event2': 1800  # 30 minutes in seconds
                }
            },
            'display': {
                'show_all_day_events': True,
                'show_completed_events': False,
                'default_view': 'week',
                'time_format': '24h'
            },
            'last_sync': 1234567890.0,
            'config_version': '1.0'
        }

    def tearDown(self):
        """Clean up temporary files after tests."""
        try:
            os.remove(self.config_path)
            os.rmdir(self.temp_dir)
        except OSError:
            pass

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        # Write sample config to file
        with open(self.config_path, 'w') as f:
            json.dump(self.sample_config, f)
        
        # Load config
        config = CalendarConfig.load(self.config_path)
        
        # Verify loaded data
        self.assertEqual(len(config.calendar_sources), 2)
        self.assertEqual(config.calendar_sources['source1'].url, 'http://test1.com/calendar.ics')
        self.assertEqual(config.notifications.default_time, timedelta(minutes=10))
        self.assertEqual(config.display.default_view, 'week')
        self.assertEqual(config.last_sync, 1234567890.0)

    def test_save_config(self):
        """Test saving configuration to file."""
        config = CalendarConfig(
            calendar_sources={
                'test': CalendarSource(
                    url='http://test.com/calendar.ics',
                    color='#0000FF',
                    enabled=True
                )
            },
            notifications=NotificationSettings(
                default_time=timedelta(minutes=15)
            ),
            display=DisplaySettings(
                default_view='month'
            )
        )
        
        # Save config
        config.save(self.config_path)
        
        # Verify saved file
        with open(self.config_path, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['calendar_sources']['test']['url'], 'http://test.com/calendar.ics')
        self.assertEqual(saved_data['notifications']['default_time'], 900.0)  # 15 minutes in seconds
        self.assertEqual(saved_data['display']['default_view'], 'month')

    def test_invalid_config(self):
        """Test handling of invalid configuration data."""
        invalid_config = {
            'calendar_sources': {
                'source1': {
                    'color': '#FF0000',  # Missing required 'url' field
                    'enabled': True
                }
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(invalid_config, f)
        
        with self.assertRaises(ConfigValidationError):
            CalendarConfig.load(self.config_path)

    def test_missing_config(self):
        """Test handling of missing configuration file."""
        # Load non-existent config (should create default)
        config = CalendarConfig.load(self.config_path)
        
        # Verify default values
        self.assertEqual(len(config.calendar_sources), 0)
        self.assertEqual(config.notifications.default_time, timedelta(minutes=10))
        self.assertTrue(config.notifications.enabled)
        self.assertEqual(config.display.default_view, 'week')
        
        # Verify file was created
        self.assertTrue(self.config_path.exists())

    def test_custom_notification_times(self):
        """Test handling of custom notification times."""
        config = CalendarConfig.load(self.config_path)
        
        # Add custom notification time
        config.notifications.custom_times['test_event'] = timedelta(minutes=5)
        config.save(self.config_path)
        
        # Reload and verify
        reloaded = CalendarConfig.load(self.config_path)
        self.assertEqual(
            reloaded.notifications.custom_times['test_event'],
            timedelta(minutes=5)
        )

    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid color format
        with self.assertRaises(ConfigValidationError):
            CalendarSource(
                url='http://test.com/calendar.ics',
                color='invalid_color',
                enabled=True
            )
        
        # Test invalid time format
        with self.assertRaises(ConfigValidationError):
            DisplaySettings(time_format='invalid_format')
        
        # Test invalid view mode
        with self.assertRaises(ConfigValidationError):
            DisplaySettings(default_view='invalid_view')

    def test_config_update(self):
        """Test updating existing configuration."""
        # Create initial config
        config = CalendarConfig.load(self.config_path)
        
        # Update settings
        config.display.show_all_day_events = False
        config.notifications.sound_enabled = False
        config.save(self.config_path)
        
        # Reload and verify updates
        updated = CalendarConfig.load(self.config_path)
        self.assertFalse(updated.display.show_all_day_events)
        self.assertFalse(updated.notifications.sound_enabled)

if __name__ == '__main__':
    unittest.main()