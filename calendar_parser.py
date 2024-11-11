# calendar_parser.py: Parses and aggregates events from .ics calendar URLs.
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
import pytz
import requests
from icalendar import Calendar
import hashlib

@dataclass
class Event:
    """Core event data structure."""
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    calendar_source: Optional[str] = None
    is_all_day: bool = False
    
    def __post_init__(self):
        """Ensure times are timezone-aware."""
        if self.start_time.tzinfo is None:
            self.start_time = pytz.UTC.localize(self.start_time)
        if self.end_time.tzinfo is None:
            self.end_time = pytz.UTC.localize(self.end_time)

class CalendarParser:
    """Handles fetching and parsing of ICS calendar data."""
    
    def __init__(self):
        self.cached_events: Dict[str, List[Event]] = {}
    
    def fetch_calendar(self, url: str, source_name: str) -> List[Event]:
        """Fetch and parse calendar from URL."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return self._parse_ics_data(response.text, source_name)
        except requests.RequestException as e:
            raise NetworkError(f"Failed to fetch calendar: {str(e)}")
    
    def _parse_ics_data(self, ics_data: str, source_name: str) -> List[Event]:
        """Parse ICS data into Event objects."""
        try:
            calendar = Calendar.from_ical(ics_data)
            events = []
            
            for component in calendar.walk('VEVENT'):
                event = self._component_to_event(component, source_name)
                if event:
                    events.append(event)
            
            return sorted(events, key=lambda x: x.start_time)
        except Exception as e:
            raise ParseError(f"Failed to parse calendar data: {str(e)}")
    
    def _component_to_event(self, component, source_name: str) -> Optional[Event]:
        """Convert an iCalendar component to an Event object."""
        try:
            start = component.get('dtstart').dt
            end = component.get('dtend').dt if component.get('dtend') else start
            
            # Generate consistent ID from event details
            id_string = f"{source_name}_{start}_{end}_{component.get('summary', '')}"
            event_id = hashlib.md5(id_string.encode()).hexdigest()
            
            return Event(
                id=event_id,
                title=str(component.get('summary', 'Untitled Event')),
                start_time=start,
                end_time=end,
                description=str(component.get('description', '')),
                location=str(component.get('location', '')),
                calendar_source=source_name,
                is_all_day=isinstance(start, datetime) is False
            )
        except Exception as e:
            # Log error but continue processing other events
            print(f"Error parsing event: {str(e)}")
            return None
    
    def aggregate_events(self, events_lists: List[List[Event]]) -> List[Event]:
        """Combine events from multiple sources, removing duplicates."""
        all_events = []
        seen_ids = set()
        
        for events in events_lists:
            for event in events:
                if event.id not in seen_ids:
                    seen_ids.add(event.id)
                    all_events.append(event)
        
        return sorted(all_events, key=lambda x: x.start_time)

# Existing exception classes
class CalendarError(Exception):
    """Base exception for calendar-related errors."""
    pass

class ParseError(CalendarError):
    """Raised when calendar parsing fails."""
    pass

class NetworkError(CalendarError):
    """Raised when calendar fetching fails."""
    pass