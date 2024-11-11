# calendar_parser.py: Parses and aggregates events from .ics calendar URLs.
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import pytz

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

class CalendarError(Exception):
    """Base exception for calendar-related errors."""
    pass

class ParseError(CalendarError):
    """Raised when calendar parsing fails."""
    pass

class NetworkError(CalendarError):
    """Raised when calendar fetching fails."""
    pass