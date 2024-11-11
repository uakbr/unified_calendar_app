from dataclasses import dataclass, field
from typing import Dict, Optional, List
import json
from pathlib import Path
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

@dataclass
class CalendarSource:
    """Configuration for a calendar source."""
    url: str
    color: str
    enabled: bool = True
    name: Optional[str] = None

@dataclass
class NotificationSettings:
    """Configuration for event notifications."""
    default_time: timedelta = field(default_factory=lambda: timedelta(minutes=10))
    enabled: bool = True
    sound_enabled: bool = True
    custom_times: Dict[str, timedelta] = field(default_factory=dict)  # event_id: time_before

@dataclass
class DisplaySettings:
    """Configuration for calendar display."""
    show_all_day_events: bool = True
    show_completed_events: bool = False
    default_view: str = "week"  # "day", "week", "month"
    time_format: str = "24h"    # "12h", "24h"

@dataclass
class CalendarConfig:
    """Complete application configuration."""
    calendar_sources: Dict[str, CalendarSource] = field(default_factory=dict)
    notifications: NotificationSettings = field(default_factory=NotificationSettings)
    display: DisplaySettings = field(default_factory=DisplaySettings)
    last_sync: Optional[float] = None
    config_version: str = "1.0"
    
    @classmethod
    def load(cls, config_path: Path = Path("config.json")) -> 'CalendarConfig':
        """Load configuration from JSON file."""
        try:
            if not config_path.exists():
                logger.info("No config file found, creating default configuration")
                config = cls()
                config.save(config_path)
                return config
            
            with config_path.open('r') as f:
                data = json.load(f)
            
            return cls._from_dict(data)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise ConfigError(f"Failed to load configuration: {str(e)}")
    
    def save(self, config_path: Path = Path("config.json")) -> None:
        """Save configuration to JSON file."""
        try:
            with config_path.open('w') as f:
                json.dump(self._to_dict(), f, indent=4)
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise ConfigError(f"Failed to save configuration: {str(e)}")
    
    @classmethod
    def _from_dict(cls, data: Dict) -> 'CalendarConfig':
        """Create configuration from dictionary."""
        try:
            return cls(
                calendar_sources={
                    source_id: CalendarSource(**source_data)
                    for source_id, source_data in data.get('calendar_sources', {}).items()
                },
                notifications=NotificationSettings(**data.get('notifications', {})),
                display=DisplaySettings(**data.get('display', {})),
                last_sync=data.get('last_sync'),
                config_version=data.get('config_version', "1.0")
            )
        except Exception as e:
            raise ConfigValidationError(f"Invalid configuration data: {str(e)}")
    
    def _to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            'calendar_sources': {
                source_id: {
                    'url': source.url,
                    'color': source.color,
                    'enabled': source.enabled,
                    'name': source.name
                }
                for source_id, source in self.calendar_sources.items()
            },
            'notifications': {
                'default_time': self.notifications.default_time.total_seconds(),
                'enabled': self.notifications.enabled,
                'sound_enabled': self.notifications.sound_enabled,
                'custom_times': {
                    event_id: time.total_seconds()
                    for event_id, time in self.notifications.custom_times.items()
                }
            },
            'display': {
                'show_all_day_events': self.display.show_all_day_events,
                'show_completed_events': self.display.show_completed_events,
                'default_view': self.display.default_view,
                'time_format': self.display.time_format
            },
            'last_sync': self.last_sync,
            'config_version': self.config_version
        }

class ConfigError(Exception):
    """Base exception for configuration-related errors."""
    pass

class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""
    pass