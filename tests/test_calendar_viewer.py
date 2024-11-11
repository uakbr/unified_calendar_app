import unittest
from datetime import datetime, timedelta, date
import pytz
from calendar_viewer import CalendarViewer
from calendar_parser import Event
from typing import List

class TestCalendarViewer(unittest.TestCase):
    def setUp(self):
        """Setup test environment before each test."""
        self.viewer = CalendarViewer()
        self.now = datetime.now(pytz.UTC)
        
        # Create sample events across different times and sources
        self.events = [
            Event(
                id="1",
                title="Past Event",
                start_time=self.now - timedelta(hours=2),
                end_time=self.now - timedelta(hours=1),
                calendar_source="source1"
            ),
            Event(
                id="2",
                title="Current Event",
                start_time=self.now - timedelta(minutes=30),
                end_time=self.now + timedelta(minutes=30),
                calendar_source="source1"
            ),
            Event(
                id="3",
                title="Future Event",
                start_time=self.now + timedelta(hours=1),
                end_time=self.now + timedelta(hours=2),
                calendar_source="source2"
            ),
            Event(
                id="4",
                title="All Day Event",
                start_time=self.now.replace(hour=0, minute=0, second=0),
                end_time=(self.now + timedelta(days=1)).replace(hour=0, minute=0, second=0),
                calendar_source="source2",
                is_all_day=True
            ),
            Event(
                id="5",
                title="Next Week Event",
                start_time=self.now + timedelta(days=7),
                end_time=self.now + timedelta(days=7, hours=1),
                calendar_source="source3"
            ),
            Event(
                id="6",
                title="Next Month Event",
                start_time=self.now + timedelta(days=32),
                end_time=self.now + timedelta(days=32, hours=2),
                calendar_source="source3"
            )
        ]
        self.viewer.set_events(self.events)

    def test_initial_state(self):
        """Test initial viewer state."""
        self.assertTrue(self.viewer.show_all_day_events)
        self.assertFalse(self.viewer.show_completed_events)
        self.assertEqual(len(self.viewer.filters), 0)
        self.assertEqual(len(self.viewer._on_update_callbacks), 0)

    def test_get_filtered_events_all_visible(self):
        """Test getting all events with no filters."""
        events = self.viewer.get_filtered_events()
        self.assertEqual(len(events), 6)
        self.assertEqual([e.id for e in events], ["1", "2", "3", "4", "5", "6"])

    def test_source_filtering(self):
        """Test filtering events by source."""
        # Test single source filter
        self.viewer.set_source_filter("source1", False)
        events = self.viewer.get_filtered_events()
        self.assertEqual(len(events), 4)
        self.assertTrue(all(e.calendar_source != "source1" for e in events))
        
        # Test multiple source filters
        self.viewer.set_source_filter("source2", False)
        events = self.viewer.get_filtered_events()
        self.assertEqual(len(events), 2)
        self.assertTrue(all(e.calendar_source == "source3" for e in events))

    def test_all_day_event_filtering(self):
        """Test filtering all-day events."""
        self.viewer.set_show_all_day_events(False)
        events = self.viewer.get_filtered_events()
        self.assertEqual(len(events), 5)
        self.assertTrue(all(not e.is_all_day for e in events))

    def test_completed_event_filtering(self):
        """Test filtering completed events."""
        self.viewer.set_show_completed_events(False)
        events = self.viewer.get_filtered_events()
        self.assertTrue(all(e.end_time >= self.now for e in events))

    def test_get_next_event(self):
        """Test getting the next upcoming event."""
        next_event = self.viewer.get_next_event()
        self.assertEqual(next_event.id, "3")  # Future Event
        
        # Test with source filtering
        self.viewer.set_source_filter("source2", False)
        next_event = self.viewer.get_next_event()
        self.assertEqual(next_event.id, "5")  # Next Week Event

    def test_get_countdown_text(self):
        """Test countdown text generation."""
        countdown = self.viewer.get_countdown_text()
        self.assertIn("Future Event", countdown)
        self.assertIn("in", countdown)
        
        # Test with no upcoming events
        self.viewer.set_events([])
        self.assertEqual(self.viewer.get_countdown_text(), "No upcoming events")

    def test_date_range_filtering(self):
        """Test getting events within date ranges."""
        # Test day range
        day_start = self.now.replace(hour=0, minute=0, second=0)
        day_end = day_start + timedelta(days=1)
        day_events = self.viewer.get_events_for_range(day_start, day_end)
        self.assertEqual(len(day_events), 4)  # Past, Current, Future, All Day
        
        # Test week range
        week_end = day_start + timedelta(days=7)
        week_events = self.viewer.get_events_for_range(day_start, week_end)
        self.assertEqual(len(week_events), 5)  # All except Next Month
        
        # Test month range
        month_end = day_start + timedelta(days=32)
        month_events = self.viewer.get_events_for_range(day_start, month_end)
        self.assertEqual(len(month_events), 6)  # All events

    def test_timezone_handling(self):
        """Test handling of events in different timezones."""
        ny_tz = pytz.timezone('America/New_York')
        tokyo_tz = pytz.timezone('Asia/Tokyo')
        
        events = [
            Event(
                id="tz1",
                title="NY Event",
                start_time=ny_tz.localize(datetime.now()),
                end_time=ny_tz.localize(datetime.now() + timedelta(hours=1)),
                calendar_source="source1"
            ),
            Event(
                id="tz2",
                title="Tokyo Event",
                start_time=tokyo_tz.localize(datetime.now()),
                end_time=tokyo_tz.localize(datetime.now() + timedelta(hours=1)),
                calendar_source="source1"
            )
        ]
        
        self.viewer.set_events(events)
        filtered_events = self.viewer.get_filtered_events()
        self.assertEqual(len(filtered_events), 2)
        
        # Verify events are properly ordered regardless of source timezone
        event_times = [e.start_time.astimezone(pytz.UTC) for e in filtered_events]
        self.assertEqual(event_times, sorted(event_times))

    def test_update_callbacks(self):
        """Test update callback notification system."""
        callback_count = 0
        
        def test_callback():
            nonlocal callback_count
            callback_count += 1
        
        self.viewer.add_update_callback(test_callback)
        
        # Test various operations that should trigger callbacks
        self.viewer.set_source_filter("source1", False)
        self.viewer.set_show_all_day_events(False)
        self.viewer.set_show_completed_events(True)
        self.viewer.set_events([])
        
        self.assertEqual(callback_count, 4)

    def test_empty_sources(self):
        """Test behavior with empty sources."""
        self.viewer.set_events([])
        self.assertEqual(len(self.viewer.get_filtered_events()), 0)
        self.assertIsNone(self.viewer.get_next_event())
        self.assertEqual(self.viewer.get_countdown_text(), "No upcoming events")
        
        # Test with filters
        self.viewer.set_source_filter("source1", False)
        self.assertEqual(len(self.viewer.get_filtered_events()), 0)

if __name__ == '__main__':
    unittest.main()