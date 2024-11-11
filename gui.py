import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import calendar
import pytz
from calendar_parser import Event
from calendar_viewer import CalendarViewer
from notification_manager import NotificationManager, NotificationPriority
from config import CalendarConfig, CalendarSource
from utils.color_utils import get_contrast_color
import logging

logger = logging.getLogger(__name__)

class CalendarGrid(ttk.Frame):
    """Custom calendar grid widget supporting day/week/month views."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.view_mode = "week"  # "day", "week", "month"
        self.current_date = datetime.now(pytz.UTC)
        self.events: List[Event] = []
        self.selected_event: Optional[Event] = None
        self._setup_grid()
        self._bind_events()
    
    def _setup_grid(self) -> None:
        """Initialize the calendar grid."""
        self.canvas = tk.Canvas(self, bg='white')
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Bind canvas resizing
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.scrollable_frame.bind('<Configure>', self._on_frame_configure)
    
    def _bind_events(self) -> None:
        """Bind mouse and keyboard events."""
        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
        
        # Keyboard navigation
        self.bind('<Left>', lambda e: self._navigate_date(-1))
        self.bind('<Right>', lambda e: self._navigate_date(1))
        self.bind('<Up>', lambda e: self._navigate_event(-1))
        self.bind('<Down>', lambda e: self._navigate_event(1))
        self.bind('<Return>', self._on_enter)
    
    def set_view_mode(self, mode: str) -> None:
        """Change the calendar view mode."""
        if mode in ["day", "week", "month"]:
            self.view_mode = mode
            self._update_view()
    
    def set_events(self, events: List[Event]) -> None:
        """Update the displayed events."""
        self.events = events
        self._update_view()
    
    def _update_view(self) -> None:
        """Redraw the calendar grid based on current view mode."""
        # Clear existing content
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if self.view_mode == "day":
            self._draw_day_view()
        elif self.view_mode == "week":
            self._draw_week_view()
        else:  # month
            self._draw_month_view()
    
    def _draw_day_view(self) -> None:
        """Draw the day view grid."""
        date = self.current_date.date()
        events = [e for e in self.events if e.start_time.date() == date]
        
        # Create hour labels and event slots
        for hour in range(24):
            time_label = ttk.Label(
                self.scrollable_frame,
                text=f"{hour:02d}:00",
                width=8
            )
            time_label.grid(row=hour, column=0, sticky="e", padx=5)
            
            # Create slot for events
            slot = ttk.Frame(self.scrollable_frame, height=60)
            slot.grid(row=hour, column=1, sticky="ew")
            slot.grid_propagate(False)
            
            # Add events that start in this hour
            for event in events:
                if event.start_time.hour == hour:
                    self._create_event_widget(event, slot)
    
    def _draw_week_view(self) -> None:
        """Draw the week view grid."""
        start_of_week = self.current_date - timedelta(days=self.current_date.weekday())
        
        # Create day headers
        for i, day in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
            date = start_of_week + timedelta(days=i)
            header = ttk.Label(
                self.scrollable_frame,
                text=f"{day}\n{date.strftime('%d/%m')}",
                width=15
            )
            header.grid(row=0, column=i+1, sticky="ew", padx=1, pady=5)
        
        # Create hour labels and event slots
        for hour in range(24):
            time_label = ttk.Label(
                self.scrollable_frame,
                text=f"{hour:02d}:00",
                width=8
            )
            time_label.grid(row=hour+1, column=0, sticky="e", padx=5)
            
            # Create slots for each day
            for day in range(7):
                date = start_of_week + timedelta(days=day)
                slot = ttk.Frame(self.scrollable_frame, height=60)
                slot.grid(row=hour+1, column=day+1, sticky="ew", padx=1)
                slot.grid_propagate(False)
                
                # Add events for this time slot
                events = [
                    e for e in self.events
                    if e.start_time.date() == date.date() and e.start_time.hour == hour
                ]
                for event in events:
                    self._create_event_widget(event, slot)
    
    def _draw_month_view(self) -> None:
        """Draw the month view grid."""
        year = self.current_date.year
        month = self.current_date.month
        cal = calendar.monthcalendar(year, month)
        
        # Create day headers
        for i, day in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
            header = ttk.Label(
                self.scrollable_frame,
                text=day,
                width=15
            )
            header.grid(row=0, column=i, sticky="ew", padx=1, pady=5)
        
        # Create day cells
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day != 0:
                    date = datetime(year, month, day, tzinfo=pytz.UTC)
                    cell = ttk.Frame(self.scrollable_frame, height=100)
                    cell.grid(row=week_num+1, column=day_num, sticky="nsew", padx=1, pady=1)
                    cell.grid_propagate(False)
                    
                    # Add date label
                    date_label = ttk.Label(cell, text=str(day))
                    date_label.pack(anchor="nw", padx=2, pady=2)
                    
                    # Add events for this day
                    events = [
                        e for e in self.events
                        if e.start_time.date() == date.date()
                    ]
                    for event in events:
                        self._create_event_widget(event, cell)
    
    def _create_event_widget(self, event: Event, parent: ttk.Frame) -> None:
        """Create a widget to display an event."""
        frame = ttk.Frame(
            parent,
            style=f"Event.TFrame",
            cursor="hand2"
        )
        frame.pack(fill="x", padx=2, pady=1)
        
        # Configure style with event color
        style = ttk.Style()
        style.configure(
            f"Event.TFrame",
            background=event.calendar_source,
            relief="raised"
        )
        
        # Event label
        label = ttk.Label(
            frame,
            text=event.title,
            foreground=get_contrast_color(event.calendar_source),
            background=event.calendar_source
        )
        label.pack(fill="x", padx=2)
        
        # Bind events
        frame.bind('<Button-1>', lambda e: self._select_event(event))
        frame.bind('<Double-Button-1>', lambda e: self._edit_event(event))
        
        # Make widget accessible
        frame.bind('<Key-Return>', lambda e: self._edit_event(event))
        frame.bind('<Key-space>', lambda e: self._select_event(event))
        
        # Set accessibility properties
        frame['aria-label'] = f"Event: {event.title}"
        frame['aria-selected'] = str(event == self.selected_event).lower()
    
    def _select_event(self, event: Event) -> None:
        """Select an event and highlight it."""
        self.selected_event = event
        self._update_view()  # Refresh to show selection
    
    def _edit_event(self, event: Event) -> None:
        """Open event editing dialog."""
        # Implementation for event editing dialog
        pass
    
    def _navigate_date(self, delta: int) -> None:
        """Navigate between dates."""
        if self.view_mode == "day":
            self.current_date += timedelta(days=delta)
        elif self.view_mode == "week":
            self.current_date += timedelta(weeks=delta)
        else:  # month
            # Add/subtract months while preserving the day
            year = self.current_date.year
            month = self.current_date.month + delta
            day = min(self.current_date.day, calendar.monthrange(year, month)[1])
            self.current_date = self.current_date.replace(year=year, month=month, day=day)
        
        self._update_view()
    
    def _navigate_event(self, delta: int) -> None:
        """Navigate between events using keyboard."""
        if not self.events:
            return
            
        if not self.selected_event:
            self._select_event(self.events[0])
            return
            
        current_index = self.events.index(self.selected_event)
        new_index = (current_index + delta) % len(self.events)
        self._select_event(self.events[new_index])
    
    def _on_canvas_configure(self, event) -> None:
        """Handle canvas resize."""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)
    
    def _on_frame_configure(self, event) -> None:
        """Update scroll region."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_click(self, event) -> None:
        """Handle mouse click."""
        # Implementation for click handling
        pass
    
    def _on_drag(self, event) -> None:
        """Handle event dragging."""
        # Implementation for drag handling
        pass
    
    def _on_release(self, event) -> None:
        """Handle drag release."""
        # Implementation for drag release
        pass
    
    def _on_enter(self, event) -> None:
        """Handle enter key press."""
        if self.selected_event:
            self._edit_event(self.selected_event)

class CalendarApp(tk.Tk):
    """Main application window."""
    
    def __init__(self, config: CalendarConfig):
        super().__init__()
        
        self.title("Privacy Calendar")
        self.geometry("1024x768")
        self.config = config
        
        # Initialize components
        self.calendar_viewer = CalendarViewer()
        self.notification_manager = NotificationManager(config.notifications)
        
        # Setup GUI
        self._setup_gui()
        self._setup_notification_handler()
        
        # Start update timer
        self._schedule_updates()
    
    def _setup_gui(self) -> None:
        """Setup the main GUI components."""
        # Create main container with toolbar and status bar
        self._setup_toolbar()
        self._setup_calendar_grid()
        self._setup_status_bar()
        self._setup_source_filters()
        
        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
    def _setup_toolbar(self) -> None:
        """Setup the application toolbar."""
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Navigation buttons
        ttk.Button(
            toolbar,
            text="Today",
            command=self._go_to_today
        ).pack(side="left", padx=5)
        
        ttk.Button(
            toolbar,
            text="<",
            command=lambda: self._navigate(-1)
        ).pack(side="left")
        
        ttk.Button(
            toolbar,
            text=">",
            command=lambda: self._navigate(1)
        ).pack(side="left", padx=5)
        
        # View selection
        self.view_var = tk.StringVar(value=self.config.display.default_view)
        for view in ['day', 'week', 'month']:
            ttk.Radiobutton(
                toolbar,
                text=view.capitalize(),
                value=view,
                variable=self.view_var,
                command=self._change_view
            ).pack(side="left", padx=5)
        
        # Settings button
        ttk.Button(
            toolbar,
            text="Settings",
            command=self._show_settings
        ).pack(side="right")
    
    def _setup_calendar_grid(self) -> None:
        """Setup the main calendar grid."""
        self.calendar_grid = CalendarGrid(self)
        self.calendar_grid.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Set initial view mode
        self.calendar_grid.set_view_mode(self.config.display.default_view)
    
    def _setup_status_bar(self) -> None:
        """Setup the status bar with countdown timer."""
        status_bar = ttk.Frame(self)
        status_bar.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        self.countdown_label = ttk.Label(
            status_bar,
            text="No upcoming events",
            font=('Helvetica', 10)
        )
        self.countdown_label.pack(side="left")
    
    def _setup_source_filters(self) -> None:
        """Setup calendar source filters."""
        filters_frame = ttk.LabelFrame(self, text="Calendars")
        filters_frame.grid(row=1, column=1, sticky="n", padx=5, pady=5)
        
        for source_id, source in self.config.calendar_sources.items():
            frame = ttk.Frame(filters_frame)
            frame.pack(fill="x", padx=5, pady=2)
            
            var = tk.BooleanVar(value=source.enabled)
            cb = ttk.Checkbutton(
                frame,
                text=source.name or source_id,
                variable=var,
                command=lambda sid=source_id, v=var: self._toggle_source(sid, v.get())
            )
            cb.pack(side="left")
            
            color_label = ttk.Label(
                frame,
                text="■",
                foreground=source.color
            )
            color_label.pack(side="right")
    
    def _setup_notification_handler(self) -> None:
        """Setup notification handling."""
        self.notification_manager.add_notification_callback(self._show_notification)
    
    def _show_notification(self, message: str, event: Event, priority: int) -> None:
        """Display a notification."""
        messagebox.showinfo("Event Reminder", message)
    
    def _schedule_updates(self) -> None:
        """Schedule periodic updates."""
        self._update_countdown()
        self.after(1000, self._schedule_updates)
    
    def _update_countdown(self) -> None:
        """Update the countdown display."""
        countdown_text = self.calendar_viewer.get_countdown_text()
        self.countdown_label.configure(text=countdown_text)
    
    def _go_to_today(self) -> None:
        """Navigate to today's date."""
        self.calendar_grid.current_date = datetime.now(pytz.UTC)
        self.calendar_grid._update_view()
    
    def _navigate(self, delta: int) -> None:
        """Navigate between dates."""
        self.calendar_grid._navigate_date(delta)
    
    def _change_view(self) -> None:
        """Change the calendar view mode."""
        self.calendar_grid.set_view_mode(self.view_var.get())
    
    def _toggle_source(self, source_id: str, visible: bool) -> None:
        """Toggle calendar source visibility."""
        self.calendar_viewer.set_source_filter(source_id, visible)
        self.calendar_grid.set_events(self.calendar_viewer.get_filtered_events())
    
    def _show_settings(self) -> None:
        """Show settings dialog."""
        # Implementation for settings dialog
        pass

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    config = CalendarConfig.load()
    
    # Start application
    app = CalendarApp(config)
    app.mainloop()