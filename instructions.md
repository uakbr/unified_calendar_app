# Project Objective

This application aggregates multiple `.ics` calendar links to create a privacy-preserving, unified calendar view with customizable notifications and display options. It stores calendar data locally to ensure privacy, showing a countdown timer to the next event, and enabling customizations such as toggling all-day events and applying color-coded filters by event source. The application allows users to manage notification times and preferences for an enhanced, personalized calendar experience.

## Technical Software Specification

### Project: Privacy-Preserving Unified Calendar Application

### Overview
This application will provide a privacy-preserving, unified calendar view by aggregating events from multiple private calendar `.ics` links, like those from Office365. The goal is to create a streamlined calendar interface that amalgamates events, offers customization features for the display, and provides user-configurable notifications. Additionally, the app will have a countdown timer to the next scheduled event.

### Requirements

1. **Privacy Preserving**: Store calendar data locally and ensure no private data is transmitted or exposed.
2. **Calendar Aggregation**: Support importing multiple `.ics` links and show all events in a unified view.
3. **Custom Notifications**: Allow users to set and configure notifications for upcoming events.
4. **Countdown Timer**: Display a timer that shows the remaining time until the next event.
5. **User Customizations**:
   - Toggle visibility for all-day events.
   - Filter events based on calendar source.
   - Provide color-coded options for differentiating events from various sources.

### Dependencies
- **Python 3.11.6** (PEP8 standards and Pylint compliance)
- **Libraries**:
  - `icalendar`: Parse and manage `.ics` files.
  - `pytz`: Handle time zones.
  - `datetime`: Manage and format date and time.
  - `APScheduler`: Schedule notifications.
  - `tkinter`: GUI for desktop application.

### Modules and Functionality

#### 1. **Event Parsing and Aggregation**
   - **Module**: `calendar_parser.py`
   - **Functionality**:
     - **Import .ics**: Parse `.ics` calendar links using `icalendar`.
     - **Event Filtering**: Extract events by type (all-day, timed events, etc.).
     - **Duplicate Handling**: Merge events from multiple calendars by unique identifiers.
   - **Output**: List of events with fields such as start time, end time, description, and location.

#### 2. **Unified Calendar Viewer**
   - **Module**: `calendar_viewer.py`
   - **Functionality**:
     - **Display Events**: Create a scrollable list or calendar grid showing all events in a unified view.
     - **Event Customization**:
       - Toggle all-day events visibility.
       - Show events color-coded by source.
       - Apply filters to show/hide specific calendar events.
     - **Next Event Timer**: Calculate and display a countdown timer for the next upcoming event.

#### 3. **Custom Notification System**
   - **Module**: `notification_manager.py`
   - **Functionality**:
     - **User Configuration**: Allow users to specify notification preferences (e.g., 5 minutes, 10 minutes before an event).
     - **Scheduling**: Use `APScheduler` to trigger notifications.
     - **Notification Display**: Show alerts or pop-ups when notifications are triggered.
   
#### 4. **Settings and Configuration**
   - **Module**: `config.py`
   - **Functionality**:
     - **Manage User Preferences**: Store settings for notification times, event filters, and visibility settings.
     - **Load and Save Configurations**: Save configuration in a JSON file to allow persistent settings.

#### 5. **GUI Interface**
   - **Module**: `gui.py`
   - **Functionality**:
     - **Main Window**: Display a unified calendar interface.
     - **Settings Window**: Include settings for notification preferences, event visibility, and customization.
     - **Next Event Countdown**: Show a live countdown in a status bar.
   - **Components**:
     - **List View/Grid**: Display events with options for daily, weekly, or monthly views.
     - **Settings Modal**: Manage user preferences for calendar display.
     - **Countdown Timer**: Show a timer at the top or bottom of the window to indicate time until the next event.

### Data Flow

1. **Data Import**: Users input `.ics` URLs, and the application retrieves calendar data via `calendar_parser.py`.
2. **Event Aggregation**: Parsed events from each calendar source are combined into a single view.
3. **User Preferences**: The app loads user preferences from `config.py` for customized display and notification settings.
4. **GUI Display**: `gui.py` renders events and customizes the interface based on user preferences.
5. **Countdown Timer**: Continuously updated timer shows time until the next event.
6. **Notification Scheduling**: Notifications are set in `notification_manager.py` based on user-configured intervals before events.

### Functions

#### calendar_parser.py
- `fetch_and_parse_ics(url: str) -> List[Event]`: Fetch and parse `.ics` data from the provided URL.
- `aggregate_events(events: List[Event]) -> List[Event]`: Remove duplicates and sort events by start time.

#### calendar_viewer.py
- `display_events(events: List[Event])`: Render events in the calendar GUI.
- `apply_filters(filters: Dict) -> List[Event]`: Filter events based on user-selected criteria.

#### notification_manager.py
- `set_notification(event: Event, time_before: timedelta)`: Schedule a notification for an event.
- `notify_user(message: str)`: Trigger a system notification or pop-up for the user.

#### config.py
- `load_config() -> Dict`: Load configuration settings from a JSON file.
- `save_config(config: Dict)`: Save updated settings to the configuration file.

#### gui.py
- `initialize_gui()`: Initialize main GUI elements.
- `show_settings_window()`: Open a settings modal to configure app preferences.
- `update_countdown_timer(next_event: Event)`: Continuously update countdown timer display.

### Error Handling
- **Network Errors**: Handle network errors for `.ics` fetching.
- **ICS Parsing Errors**: Use fallback options if `.ics` data is incomplete or unreadable.
- **Notification Errors**: Log or silently handle errors related to notification scheduling.

### Testing
- Unit tests for each module.
- Integration tests for data flow between modules.
- GUI testing for correct display and updates on user actions.

This specification provides a comprehensive view of the requirements, modules, and key functionalities for building a privacy-preserving, unified calendar application with customizable notifications and display options.

```plaintext
.
├── calendar_parser.py           # Parses and aggregates events from .ics calendar URLs.
├── calendar_viewer.py           # Manages the display of events in a unified view and handles event customizations.
├── notification_manager.py      # Sets and triggers user-configured notifications for events.
├── config.py                    # Loads and saves user preferences for calendar display and notifications.
├── gui.py                       # Constructs the GUI interface for displaying events, timer, and settings.
├── main.py                      # Entry point to initialize and run the application.
├── utils
│   ├── timer_utils.py           # Utility functions to calculate and display time until the next event.
│   └── color_utils.py           # Utility functions to handle color coding of events by source.
├── assets
│   └── icon.png                 # Icon for the application window and notifications.
├── config.json                  # JSON file to store user configuration settings.
├── README.md                    # Documentation outlining setup, usage, and features of the application.
└── tests
    ├── test_calendar_parser.py  # Unit tests for calendar parsing and aggregation.
    ├── test_calendar_viewer.py  # Unit tests for event display and customization options.
    ├── test_notification_manager.py  # Unit tests for the notification scheduling system.
    ├── test_config.py           # Tests for loading and saving user configurations.
    └── test_gui.py              # GUI component testing for display and user interaction.
```

### File Explanations

- **calendar_parser.py**: Manages `.ics` data parsing from URLs, handles event extraction, and performs duplicate event checks.
- **calendar_viewer.py**: Displays events in a unified view, applies filters, and manages user customizations like toggling all-day events.
- **notification_manager.py**: Sets notifications using APScheduler based on user preferences, triggers alerts, and ensures notifications are accurate.
- **config.py**: Loads and saves configuration settings in JSON format, enabling persistent user preferences across sessions.
- **gui.py**: Implements the main graphical interface using Tkinter, including the event list, settings modal, and countdown timer for the next event.
- **main.py**: Initializes the application, loading settings and displaying the unified calendar view.
- **utils/timer_utils.py**: Provides helper functions for countdown timer calculations and display updates.
- **utils/color_utils.py**: Handles color coding of events based on source calendars, enabling user differentiation.
- **assets/icon.png**: Icon asset for the application, displayed in the app and used for notifications.
- **config.json**: Stores user-specific settings like notification preferences, visibility filters, and customization options.
- **README.md**: Documentation detailing the application’s setup, usage, configuration, and feature list.
- **tests/**: Contains unit and integration tests for each module, ensuring the functionality of event parsing, notifications, configurations, and GUI operations.

