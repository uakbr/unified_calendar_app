from typing import List, Dict, Optional, Callable
from datetime import datetime
import pytz
from calendar_parser import Event
from utils.timer_utils import calculate_time_until, format_countdown

class CalendarViewer:
    """Manages the display and filtering of calendar events."""
    
    def __init__(self):
        self.events: List[Event] = []
        self.filters: Dict[str, bool] = {}  # source_id: visibility
        self.show_all_day_events: bool = True
        self.show_completed_events: bool = False
        self._on_update_callbacks: List[Callable] = []
    
    def set_events(self, events: List[Event]) -> None:
        """Update the events list and notify listeners."""
        self.events = sorted(events, key=lambda x: x.start_time)
        self._notify_update()
    
    def add_update_callback(self, callback: Callable[[], None]) -> None:
        """Add a callback to be notified of display updates."""
        self._on_update_callbacks.append(callback)
    
    def _notify_update(self) -> None:
        """Notify all registered callbacks of an update."""
        for callback in self._on_update_callbacks:
            callback()
    
    def get_filtered_events(self) -> List[Event]:
        """Get events based on current filters and settings."""
        now = datetime.now(pytz.UTC)
        filtered_events = []
        
        for event in self.events:
            # Check source filter
            if event.calendar_source and not self.filters.get(event.calendar_source, True):
                continue
                
            # Check all-day filter
            if event.is_all_day and not self.show_all_day_events:
                continue
                
            # Check completed filter
            if not self.show_completed_events and event.end_time < now:
                continue
                
            filtered_events.append(event)
        
        return filtered_events
    
    def get_next_event(self) -> Optional[Event]:
        """Get the next upcoming event based on current filters."""
        now = datetime.now(pytz.UTC)
        future_events = [
            event for event in self.get_filtered_events()
            if event.start_time > now
        ]
        return future_events[0] if future_events else None
    
    def get_countdown_text(self) -> str:
        """Get formatted countdown to next event."""
        next_event = self.get_next_event()
        if not next_event:
            return "No upcoming events"
        
        time_until = calculate_time_until(next_event.start_time)
        return f"Next: {next_event.title} in {format_countdown(time_until)}"
    
    def set_source_filter(self, source_id: str, visible: bool) -> None:
        """Set visibility filter for a calendar source."""
        self.filters[source_id] = visible
        self._notify_update()
    
    def set_show_all_day_events(self, show: bool) -> None:
        """Set visibility of all-day events."""
        self.show_all_day_events = show
        self._notify_update()
    
    def set_show_completed_events(self, show: bool) -> None:
        """Set visibility of completed events."""
        self.show_completed_events = show
        self._notify_update()
    
    def get_events_for_date(self, date: datetime) -> List[Event]:
        """Get filtered events for a specific date."""
        target_date = date.date()
        return [
            event for event in self.get_filtered_events()
            if event.start_time.date() == target_date
        ]
    
    def get_events_for_range(self, start: datetime, end: datetime) -> List[Event]:
        """Get filtered events within a date range."""
        return [
            event for event in self.get_filtered_events()
            if start <= event.start_time <= end
        ]