import unittest
from datetime import datetime, timedelta
import pytz
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
from gui import CalendarApp, EventDetailsDialog
from calendar_parser import Event
from config import CalendarConfig, CalendarSource, NotificationSettings, DisplaySettings

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
            notifications=NotificationSettings(
                default_time=timedelta(minutes=10),
                enabled=True,
                sound_enabled=True
            ),
            display=DisplaySettings(
                show_all_day_events=True,
                show_completed_events=False,
                default_view='week',
                time_format='24h'
            )
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

    def test_event_list_display(self):
        """Test event list display and updates."""
        # Set events
        self.app.calendar_viewer.set_events(self.test_events)
        self.app.update_event_list()
        
        # Verify events are displayed
        displayed_events = [item['values'][1] for item in self.app.event_tree.get_children()]
        self.assertEqual(len(displayed_events), 2)
        self.assertIn("Test Event 1", displayed_events)
        self.assertIn("All Day Event", displayed_events)

    def test_countdown_timer(self):
        """Test countdown timer updates."""
        self.app.calendar_viewer.set_events(self.test_events)
        self.app.update_countdown()
        
        countdown_text = self.app.countdown_label.cget("text")
        self.assertIn("Test Event 1", countdown_text)
        self.assertIn("in", countdown_text)

    @patch('tkinter.messagebox.askyesno')
    def test_source_removal(self, mock_askyesno):
        """Test calendar source removal."""
        mock_askyesno.return_value = True
        
        # Add source and verify
        self.assertTrue('test_source' in self.app.config.calendar_sources)
        
        # Remove source
        self.app._remove_calendar_source('test_source')
        
        # Verify removal
        self.assertFalse('test_source' in self.app.config.calendar_sources)

    def test_event_details_dialog(self):
        """Test event details dialog display."""
        event = self.test_events[0]
        dialog = EventDetailsDialog(self.root, event)
        
        # Verify event details are displayed correctly
        dialog_text = dialog.winfo_children()[0].winfo_children()
        text_content = ' '.join(child.cget('text') for child in dialog_text if hasattr(child, 'cget'))
        
        self.assertIn(event.title, text_content)
        self.assertIn(event.location, text_content)
        self.assertIn(event.description, text_content)

    def test_view_mode_switching(self):
        """Test switching between different calendar views."""
        # Test day view
        self.app._switch_view('day')
        self.assertEqual(self.app.current_view, 'day')
        
        # Test week view
        self.app._switch_view('week')
        self.assertEqual(self.app.current_view, 'week')
        
        # Test month view
        self.app._switch_view('month')
        self.assertEqual(self.app.current_view, 'month')

    def test_settings_dialog(self):
        """Test settings dialog functionality."""
        with patch('tkinter.Toplevel') as mock_toplevel:
            mock_dialog = MagicMock()
            mock_toplevel.return_value = mock_dialog
            
            self.app.show_settings()
            
            # Verify settings dialog creation
            mock_toplevel.assert_called_once()
            
            # Simulate settings change
            self.app.config.display.time_format = '12h'
            self.app._apply_settings()
            
            # Verify update
            self.assertEqual(self.app.config.display.time_format, '12h')

    def test_notification_handling(self):
        """Test notification system integration."""
        # Mock notification callback
        mock_callback = Mock()
        self.app.notification_manager.add_notification_callback(mock_callback)
        
        # Add event and trigger notification
        event = self.test_events[0]
        self.app.notification_manager._trigger_notification(
            event,
            priority=1,
            scheduled_time=self.now
        )
        
        # Verify callback was called
        mock_callback.assert_called_once()
        args = mock_callback.call_args[0]
        self.assertIn(event.title, args[0])  # message
        self.assertEqual(args[1], event)      # event
        self.assertEqual(args[2], 1)          # priority

    def test_error_handling(self):
        """Test GUI error handling."""
        # Test invalid calendar source
        with patch('calendar_parser.CalendarParser.fetch_calendar') as mock_fetch:
            mock_fetch.side_effect = Exception("Test error")
            
            with patch('tkinter.messagebox.showerror') as mock_error:
                self.app._fetch_calendar_data()
                mock_error.assert_called_once()

    def test_font_size_controls(self):
        """Test font size adjustment controls."""
        initial_size = tk.font.nametofont("TkDefaultFont").cget("size")
        
        # Test increase
        self.app._increase_font_size()
        new_size = tk.font.nametofont("TkDefaultFont").cget("size")
        self.assertEqual(new_size, initial_size + 2)
        
        # Test decrease
        self.app._decrease_font_size()
        final_size = tk.font.nametofont("TkDefaultFont").cget("size")
        self.assertEqual(final_size, initial_size)

if __name__ == '__main__':
    unittest.main()