import unittest
from datetime import datetime, timedelta, date
import pytz
from calendar_parser import CalendarParser, Event, ParseError, NetworkError
from unittest.mock import patch, MagicMock

class TestCalendarParser(unittest.TestCase):
    def setUp(self):
        self.parser = CalendarParser()
        self.sample_ics = """
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Test Event
DTSTART:20240315T100000Z
DTEND:20240315T110000Z
DESCRIPTION:Test Description
LOCATION:Test Location
END:VEVENT
END:VCALENDAR
"""
        self.recurring_ics = """
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Recurring Event
DTSTART:20240315T100000Z
DTEND:20240315T110000Z
RRULE:FREQ=WEEKLY;COUNT=4
END:VEVENT
END:VCALENDAR
"""
        self.all_day_ics = """
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:All Day Event
DTSTART;VALUE=DATE:20240315
DTEND;VALUE=DATE:20240316
END:VEVENT
END:VCALENDAR
"""

    def test_parse_valid_ics(self):
        """Test parsing valid ICS data."""
        events = self.parser._parse_ics_data(self.sample_ics, "test_source")
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.title, "Test Event")
        self.assertEqual(event.location, "Test Location")
        self.assertEqual(event.description, "Test Description")
        self.assertEqual(event.calendar_source, "test_source")
        self.assertTrue(isinstance(event.start_time, datetime))
        self.assertTrue(event.start_time.tzinfo is not None)

    def test_parse_recurring_event(self):
        """Test parsing recurring events."""
        events = self.parser._parse_ics_data(self.recurring_ics, "test_source")
        self.assertEqual(len(events), 4)  # Should expand to 4 instances
        
        # Verify weekly recurrence
        for i in range(1, len(events)):
            time_diff = events[i].start_time - events[i-1].start_time
            self.assertEqual(time_diff.days, 7)

    def test_parse_all_day_event(self):
        """Test parsing all-day events."""
        events = self.parser._parse_ics_data(self.all_day_ics, "test_source")
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertTrue(event.is_all_day)
        self.assertTrue(isinstance(event.start_time, datetime))
        self.assertEqual(event.start_time.hour, 0)
        self.assertEqual(event.start_time.minute, 0)

    def test_timezone_handling(self):
        """Test timezone conversion and handling."""
        local_tz_ics = """
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Local Time Event
DTSTART;TZID=America/New_York:20240315T100000
DTEND;TZID=America/New_York:20240315T110000
END:VEVENT
END:VCALENDAR
"""
        events = self.parser._parse_ics_data(local_tz_ics, "test_source")
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.start_time.tzinfo, pytz.UTC)

    @patch('requests.get')
    def test_fetch_calendar_success(self, mock_get):
        """Test successful calendar fetching."""
        mock_get.return_value.text = self.sample_ics
        mock_get.return_value.raise_for_status = MagicMock()
        
        events = self.parser.fetch_calendar("http://test.url", "test_source")
        self.assertEqual(len(events), 1)
        mock_get.assert_called_once_with("http://test.url", timeout=10)

    @patch('requests.get')
    def test_fetch_calendar_network_error(self, mock_get):
        """Test handling of network errors."""
        mock_get.side_effect = Exception("Network error")
        
        with self.assertRaises(NetworkError):
            self.parser.fetch_calendar("http://test.url", "test_source")

    def test_parse_invalid_ics(self):
        """Test handling of invalid ICS data."""
        test_cases = [
            "Invalid ICS Data",
            "BEGIN:VCALENDAR\nInvalid Content\nEND:VCALENDAR",
            "",
            "BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR",  # Empty calendar
            "BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nEND:VCALENDAR"  # Incomplete event
        ]
        
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                with self.assertRaises(ParseError):
                    self.parser._parse_ics_data(test_case, "test_source")

    def test_unicode_handling(self):
        """Test handling of unicode characters in event data."""
        unicode_ics = """
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Test 🎉 Event
LOCATION:Café
DESCRIPTION:Unicode ♥ test
DTSTART:20240315T100000Z
DTEND:20240315T110000Z
END:VEVENT
END:VCALENDAR
"""
        events = self.parser._parse_ics_data(unicode_ics, "test_source")
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.title, "Test 🎉 Event")
        self.assertEqual(event.location, "Café")
        self.assertEqual(event.description, "Unicode ♥ test")

    def test_aggregate_events(self):
        """Test event aggregation and deduplication."""
        # Create events with same and different IDs
        events = [
            [Event(
                id="1",
                title="Event 1",
                start_time=datetime.now(pytz.UTC),
                end_time=datetime.now(pytz.UTC) + timedelta(hours=1),
                calendar_source="source1"
            )],
            [Event(
                id="2",
                title="Event 2",
                start_time=datetime.now(pytz.UTC),
                end_time=datetime.now(pytz.UTC) + timedelta(hours=1),
                calendar_source="source2"
            )],
            [Event(
                id="1",  # Duplicate ID
                title="Event 1 Duplicate",
                start_time=datetime.now(pytz.UTC),
                end_time=datetime.now(pytz.UTC) + timedelta(hours=1),
                calendar_source="source3"
            )]
        ]
        
        result = self.parser.aggregate_events(events)
        self.assertEqual(len(result), 2)  # Should remove duplicate
        self.assertEqual({e.id for e in result}, {"1", "2"})

    def test_cache_behavior(self):
        """Test calendar caching behavior."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.text = self.sample_ics
            mock_get.return_value.raise_for_status = MagicMock()
            
            # First fetch should cache
            events1 = self.parser.fetch_calendar("http://test.url", "test_source")
            self.assertEqual(len(self.parser.cached_events), 1)
            
            # Second fetch should use cache
            events2 = self.parser.fetch_calendar("http://test.url", "test_source")
            mock_get.assert_called_once()  # Should only call once due to caching
            self.assertEqual(events1, events2)

if __name__ == '__main__':
    unittest.main()