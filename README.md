# Calendar Application

A unified calendar application that aggregates multiple calendar sources and provides customizable notifications.

## Features

- **Multiple Calendar Support**: Aggregate events from multiple iCal (.ics) sources
- **Smart Notifications**: Customizable notification times with priority levels
- **Flexible Display**: Day, week, and month views with customizable filters
- **Event Management**: 
  - View detailed event information
  - Filter by calendar source
  - Toggle all-day and completed events
- **Accessibility**: 
  - Adjustable font sizes
  - High contrast color schemes
  - Keyboard navigation support

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/calendar-app.git
   cd calendar-app
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

## Configuration

The application uses a `config.json` file for storing settings. Key configuration options:

- **Calendar Sources**: Add multiple calendar URLs with custom colors
- **Notifications**: Set default notification times and sound preferences
- **Display**: Customize view modes and time format
- **Filters**: Configure default visibility settings

Example configuration:


```json
{
"calendar_sources": {
"work": {
"url": "https://example.com/work.ics",
"color": "#4285F4",
"enabled": true,
"name": "Work Calendar"
}
},
"notifications": {
"default_time": 600,
"enabled": true
}
}
```

## Usage

1. **Adding Calendars**:
   - Click Settings > Add Calendar
   - Enter the calendar URL and customize display options

2. **Viewing Events**:
   - Switch between day/week/month views
   - Filter events using the sidebar toggles
   - Click events for detailed information

3. **Notifications**:
   - Set default notification times in Settings
   - Customize notifications per event
   - Enable/disable sound notifications

4. **Customization**:
   - Adjust font sizes using Ctrl+/Ctrl-
   - Toggle dark/light mode
   - Customize color schemes

## Development

### Project Structure

```plaintext
calendar-app/
├── main.py # Application entry point
├── gui.py # Main GUI implementation
├── calendar_parser.py # ICS parsing and event management
├── calendar_viewer.py # Event display and filtering
├── notification_manager.py # Notification system
├── config.py # Configuration management
├── utils/
│ ├── timer_utils.py # Time calculation utilities
│ └── color_utils.py # Color management utilities
├── tests/ # Unit and integration tests
├── assets/ # Application resources
└── config.json # User configuration file
```

### Running Tests

To run the tests, use the following command:

```
python -m unittest discover tests/
```


## Requirements

- Python 3.8+
- Required packages:
  - tkinter
  - icalendar
  - requests
  - pytz
  - apscheduler

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Calendar parsing powered by icalendar
- Scheduling system using APScheduler
- UI implemented with tkinter

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.