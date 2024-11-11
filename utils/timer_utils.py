from datetime import datetime, timedelta
import pytz

def calculate_time_until(target_time: datetime) -> timedelta:
    """Calculate time remaining until target datetime."""
    now = datetime.now(pytz.UTC)
    if target_time.tzinfo is None:
        target_time = pytz.UTC.localize(target_time)
    return target_time - now

def format_countdown(td: timedelta) -> str:
    """Format timedelta into human-readable countdown string."""
    total_seconds = int(td.total_seconds())
    
    if total_seconds < 0:
        return "Event has passed"
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"