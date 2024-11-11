from dataclasses import dataclass
from typing import Dict, Optional
import json
from pathlib import Path

@dataclass
class CalendarConfig:
    """Core configuration data structure."""
    notification_time: int = 10  # minutes before event
    show_all_day_events: bool = True
    calendar_sources: Dict[str, str] = None  # source_name: color
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CalendarConfig':
        """Create config from dictionary."""
        return cls(
            notification_time=data.get('notification_time', 10),
            show_all_day_events=data.get('show_all_day_events', True),
            calendar_sources=data.get('calendar_sources', {})
        )
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary."""
        return {
            'notification_time': self.notification_time,
            'show_all_day_events': self.show_all_day_events,
            'calendar_sources': self.calendar_sources or {}
        }

class ConfigError(Exception):
    """Base exception for configuration-related errors."""
    pass

class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""
    pass