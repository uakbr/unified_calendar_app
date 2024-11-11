import unittest
from datetime import datetime, timedelta
import pytz
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock, call
from gui import CalendarApp, EventDetailsDialog
from calendar_parser import Event
from config import CalendarConfig, CalendarSource, NotificationSettings, DisplaySettings
from utils.color_utils import get_contrast_color

class TestGUI(unittest.TestCase):
    def setUp(self):
        """Setup test environment before each test."""
        self.root = tk.Tk()
        self.config = CalendarConfig(
            calendar_sources={
                'test_source': CalendarSource(
                    url='http://test.com/calendar.ics',
                    color='#FF0000',
                    enabled=True,
                    name='Test Calendar'
                )
            },
            notifications=NotificationSettings(),
            display=DisplaySettings()
        )
        self.app = CalendarApp(self.config)
        
        # Sample events
        self.now = datetime.now(pytz.UTC)
        self.test_events = [
            Event(
                id="1",
                title="Test Event 1",
                start_time=self.now + timedelta(hours=1),
                end_time=self.now + timedelta(hours=2),
                location="Test Location",
                description="Test Description",
                calendar_source="test_source"
            ),
            Event(
                id="2",
                title="All Day Event",
                start_time=self.now.replace(hour=0, minute=0, second=0),
                end_time=(self.now + timedelta(days=1)).replace(hour=0, minute=0, second=0),
                calendar_source="test_source",
                is_all_day=True
            )
        ]

    def tearDown(self):
        """Clean up after each test."""
        self.root.destroy()

    def test_event_selection(self):
        """Test event selection and details display."""
        self.app.calendar_viewer.set_events(self.test_events)
        self.app.update_event_list()
        
        # Simulate event selection
        event_id = self.app.event_tree.get_children()[0]
        self.app.event_tree.selection_set(event_id)
        self.app.event_tree.event_generate('<<TreeviewSelect>>')
        
        # Verify details update
        details_text = self.app.details_text.get("1.0", tk.END)
        self.assertIn("Test Event 1", details_text)
        self.assertIn("Test Location", details_text)
        self.assertIn("Test Description", details_text)

    @patch('tkinter.messagebox.askyesno')
    def test_calendar_source_management(self, mock_askyesno):
        """Test calendar source addition and removal."""
        mock_askyesno.return_value = True
        
        # Test source addition
        new_source = CalendarSource(
            url='http://new.com/calendar.ics',
            color='#00FF00',
            enabled=True,
            name='New Calendar'
        )
        self.app._add_calendar_source('new_source', new_source)
        self.assertIn('new_source', self.app.config.calendar_sources)
        
        # Test source removal
        self.app._remove_calendar_source('new_source')
        self.assertNotIn('new_source', self.app.config.calendar_sources)

    def test_event_filtering(self):
        """Test event filtering controls."""
        self.app.calendar_viewer.set_events(self.test_events)
        
        # Test source filter
        self.app._toggle_source('test_source')
        filtered_events = self.app.calendar_viewer.get_filtered_events()
        self.assertEqual(len(filtered_events), 0)
        
        # Test all-day filter
        self.app._toggle_all_day_events()
        self.app._toggle_source('test_source')  # Re-enable source
        filtered_events = self.app.calendar_viewer.get_filtered_events()
        self.assertEqual(len(filtered_events), 1)
        self.assertFalse(any(e.is_all_day for e in filtered_events))

    @patch('tkinter.Toplevel')
    def test_settings_dialog(self, mock_toplevel):
        """Test settings dialog functionality."""
        mock_dialog = MagicMock()
        mock_toplevel.return_value = mock_dialog
        
        # Test settings dialog creation
        self.app.show_settings()
        mock_toplevel.assert_called_once()
        
        # Test settings update
        self.app.config.display.time_format = '12h'
        self.app._apply_settings()
        self.assertEqual(self.app.config.display.time_format, '12h')

    def test_keyboard_navigation(self):
        """Test keyboard navigation functionality."""
        self.app.calendar_viewer.set_events(self.test_events)
        self.app.update_event_list()
        
        # Test event list navigation
        self.app.event_tree.focus_set()
        self.app.event_tree.event_generate('<Down>')
        
        selected = self.app.event_tree.selection()
        self.assertEqual(len(selected), 1)
        
        # Test keyboard shortcuts
        with patch.object(self.app, '_increase_font_size') as mock_increase:
            self.app.event_generate('<Control-plus>')
            mock_increase.assert_called_once()

    def test_accessibility_features(self):
        """Test accessibility features."""
        # Test color contrast
        for source_id, source in self.app.config.calendar_sources.items():
            contrast_color = get_contrast_color(source.color)
            luminance_diff = abs(
                sum(int(source.color[i:i+2], 16) for i in (1,3,5)) / 3 -
                sum(int(contrast_color[i:i+2], 16) for i in (1,3,5)) / 3
            )
            self.assertGreater(luminance_diff, 128)  # Ensure sufficient contrast

    def test_event_details_dialog(self):
        """Test event details dialog."""
        event = self.test_events[0]
        
        with patch('tkinter.Toplevel') as mock_toplevel:
            mock_dialog = MagicMock()
            mock_toplevel.return_value = mock_dialog
            
            dialog = EventDetailsDialog(self.root, event)
            
            # Verify dialog creation
            mock_toplevel.assert_called_once()
            
            # Test dialog content
            dialog_calls = mock_dialog.method_calls
            title_calls = [call for call in dialog_calls if 'title' in str(call)]
            self.assertTrue(any('Test Event 1' in str(call) for call in title_calls))

    def test_error_handling(self):
        """Test GUI error handling."""
        # Test calendar fetch error
        with patch('calendar_parser.CalendarParser.fetch_calendar') as mock_fetch:
            mock_fetch.side_effect = Exception("Test error")
            
            with patch('tkinter.messagebox.showerror') as mock_error:
                self.app._fetch_calendar_data()
                mock_error.assert_called_once()
        
        # Test settings save error
        with patch('config.CalendarConfig.save') as mock_save:
            mock_save.side_effect = Exception("Save error")
            
            with patch('tkinter.messagebox.showerror') as mock_error:
                self.app._save_settings()
                mock_error.assert_called_once()

    def test_view_updates(self):
        """Test view update mechanisms."""
        with patch.object(self.app, 'update_event_list') as mock_update:
            # Test automatic updates
            self.app.calendar_viewer.set_events(self.test_events)
            mock_update.assert_called_once()
            
            # Test manual refresh
            self.app._refresh_display()
            self.assertEqual(mock_update.call_count, 2)

if __name__ == '__main__':
    unittest.main()