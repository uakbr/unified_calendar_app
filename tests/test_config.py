import unittest
from pathlib import Path
import json
from datetime import timedelta
import tempfile
import os
from unittest.mock import patch, mock_open
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
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
        
        # Sample valid configuration
        self.sample_config = {
            'calendar_sources': {
                'source1': {
                    'url': 'http://test1.com/calendar.ics',
                    'color': '#FF0000',
                    'enabled': True,
                    'name': 'Test Calendar 1'
                }
            },
            'notifications': {
                'default_time': 600,
                'enabled': True,
                'sound_enabled': True,
                'custom_times': {
                    'event1': 300
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

    def test_color_validation(self):
        """Test color format validation."""
        # Valid colors
        valid_colors = ['#FF0000', '#00ff00', '#0000FF', '#123456']
        for color in valid_colors:
            source = CalendarSource(url='http://test.com', color=color)
            self.assertEqual(source.color, color)

        # Invalid colors
        invalid_colors = ['FF0000', '#FFG000', '#FF00', '#FF0000FF', 'red']
        for color in invalid_colors:
            with self.assertRaises(ConfigValidationError):
                CalendarSource(url='http://test.com', color=color)

    def test_time_format_validation(self):
        """Test time format validation."""
        # Valid formats
        valid_formats = ['12h', '24h']
        for format in valid_formats:
            settings = DisplaySettings(time_format=format)
            self.assertEqual(settings.time_format, format)

        # Invalid format
        with self.assertRaises(ConfigValidationError):
            DisplaySettings(time_format='invalid')

    def test_view_mode_validation(self):
        """Test view mode validation."""
        # Valid views
        valid_views = ['day', 'week', 'month']
        for view in valid_views:
            settings = DisplaySettings(default_view=view)
            self.assertEqual(settings.default_view, view)

        # Invalid view
        with self.assertRaises(ConfigValidationError):
            DisplaySettings(default_view='invalid')

    def test_version_compatibility(self):
        """Test configuration version handling."""
        # Test current version
        config = CalendarConfig.load(self.config_path)
        self.assertEqual(config.config_version, '1.0')

        # Test loading older version
        old_config = self.sample_config.copy()
        old_config['config_version'] = '0.9'
        with open(self.config_path, 'w') as f:
            json.dump(old_config, f)
        
        config = CalendarConfig.load(self.config_path)
        self.assertEqual(config.config_version, '1.0')  # Should upgrade

    def test_malformed_json(self):
        """Test handling of malformed JSON."""
        # Test invalid JSON
        with open(self.config_path, 'w') as f:
            f.write('{"invalid": json}')
        
        with self.assertRaises(ConfigError):
            CalendarConfig.load(self.config_path)

    def test_missing_fields(self):
        """Test handling of missing required fields."""
        # Test missing required fields
        invalid_configs = [
            {},  # Empty config
            {'calendar_sources': {}},  # Missing other sections
            {'notifications': {'default_time': -1}},  # Invalid time
        ]
        
        for invalid_config in invalid_configs:
            with open(self.config_path, 'w') as f:
                json.dump(invalid_config, f)
            
            with self.assertRaises((ConfigError, ConfigValidationError)):
                CalendarConfig.load(self.config_path)

    @patch('pathlib.Path.open', side_effect=PermissionError)
    def test_file_permissions(self, mock_open):
        """Test handling of file permission errors."""
        with self.assertRaises(ConfigError):
            CalendarConfig.load(self.config_path)

    def test_custom_notification_times(self):
        """Test custom notification time validation."""
        settings = NotificationSettings()
        
        # Valid times
        settings.custom_times['event1'] = timedelta(minutes=5)
        settings.custom_times['event2'] = timedelta(hours=1)
        
        # Invalid times
        with self.assertRaises(ConfigValidationError):
            settings.custom_times['event3'] = timedelta(minutes=-5)

    def test_config_serialization(self):
        """Test configuration serialization/deserialization."""
        original_config = CalendarConfig(
            calendar_sources={
                'test': CalendarSource(
                    url='http://test.com',
                    color='#FF0000',
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
        
        # Save and reload
        original_config.save(self.config_path)
        loaded_config = CalendarConfig.load(self.config_path)
        
        # Verify equality
        self.assertEqual(
            original_config.calendar_sources['test'].url,
            loaded_config.calendar_sources['test'].url
        )
        self.assertEqual(
            original_config.notifications.default_time,
            loaded_config.notifications.default_time
        )
        self.assertEqual(
            original_config.display.default_view,
            loaded_config.display.default_view
        )

    def test_config_update(self):
        """Test configuration updates."""
        config = CalendarConfig.load(self.config_path)
        
        # Add new source
        config.calendar_sources['new_source'] = CalendarSource(
            url='http://new.com',
            color='#00FF00'
        )
        
        # Update notification settings
        config.notifications.default_time = timedelta(minutes=30)
        config.notifications.sound_enabled = False
        
        # Save and verify
        config.save(self.config_path)
        updated = CalendarConfig.load(self.config_path)
        
        self.assertEqual(len(updated.calendar_sources), 1)
        self.assertEqual(updated.notifications.default_time, timedelta(minutes=30))
        self.assertFalse(updated.notifications.sound_enabled)

if __name__ == '__main__':
    unittest.main()