import unittest
from datetime import datetime, timedelta
import pytz
from utils.timer_utils import calculate_time_until, format_countdown

class TestTimerUtils(unittest.TestCase):
    def setUp(self):
        """Setup test environment before each test."""
        self.now = datetime.now(pytz.UTC)
        self.future_times = {
            'seconds': self.now + timedelta(seconds=30),
            'minutes': self.now + timedelta(minutes=45),
            'hours': self.now + timedelta(hours=2, minutes=30),
            'days': self.now + timedelta(days=3, hours=12)
        }

    def test_calculate_time_until(self):
        """Test time until calculation."""
        # Test future times
        for key, target_time in self.future_times.items():
            time_until = calculate_time_until(target_time)
            self.assertGreater(time_until.total_seconds(), 0)
            
        # Test past time
        past_time = self.now - timedelta(minutes=30)
        time_until = calculate_time_until(past_time)
        self.assertLess(time_until.total_seconds(), 0)
        
        # Test timezone handling
        local_time = datetime.now()
        utc_time = calculate_time_until(local_time)
        self.assertIsNotNone(utc_time)

    def test_format_countdown(self):
        """Test countdown formatting."""
        # Test seconds only
        td = timedelta(seconds=45)
        self.assertEqual(format_countdown(td), "45s")
        
        # Test minutes and seconds
        td = timedelta(minutes=5, seconds=30)
        self.assertEqual(format_countdown(td), "5m 30s")
        
        # Test hours, minutes, and seconds
        td = timedelta(hours=2, minutes=15, seconds=10)
        self.assertEqual(format_countdown(td), "2h 15m 10s")
        
        # Test days, hours, and minutes
        td = timedelta(days=3, hours=12, minutes=30)
        self.assertEqual(format_countdown(td), "3d 12h 30m")
        
        # Test negative time (past event)
        td = timedelta(seconds=-30)
        self.assertEqual(format_countdown(td), "Event has passed")

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test zero duration
        td = timedelta(seconds=0)
        self.assertEqual(format_countdown(td), "0s")
        
        # Test exactly one day
        td = timedelta(days=1)
        self.assertEqual(format_countdown(td), "1d 0h 0m")
        
        # Test exactly one hour
        td = timedelta(hours=1)
        self.assertEqual(format_countdown(td), "1h 0m 0s")
        
        # Test exactly one minute
        td = timedelta(minutes=1)
        self.assertEqual(format_countdown(td), "1m 0s")

    def test_timezone_handling(self):
        """Test timezone awareness and conversion."""
        # Test with different timezones
        pacific = pytz.timezone('US/Pacific')
        eastern = pytz.timezone('US/Eastern')
        
        pacific_time = pacific.localize(datetime.now())
        eastern_time = eastern.localize(datetime.now())
        
        # Calculate time until both
        pacific_delta = calculate_time_until(pacific_time)
        eastern_delta = calculate_time_until(eastern_time)
        
        # Verify timezone conversion worked
        self.assertIsInstance(pacific_delta, timedelta)
        self.assertIsInstance(eastern_delta, timedelta)

if __name__ == '__main__':
    unittest.main() 