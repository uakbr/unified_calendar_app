import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import calendar
import pytz
from calendar_parser import Event
from calendar_viewer import CalendarViewer
from notification_manager import NotificationManager, NotificationPriority
from config import CalendarConfig, CalendarSource, DisplaySettings, NotificationSettings
from utils.color_utils import get_contrast_color
import logging

logger = logging.getLogger(__name__)

class EventDetailsDialog(tk.Toplevel):
    """Dialog for displaying detailed event information."""
    
    def __init__(self, parent, event: Event):
        super().__init__(parent)
        self.event = event
        self.title("Event Details")
        self.geometry("400x500")
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        
        # Center dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
    
    def _setup_ui(self) -> None:
        """Setup the event details UI."""
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(
            frame,
            text=self.event.title,
            font=('Helvetica', 14, 'bold'),
            wraplength=360
        ).pack(pady=(0, 10))
        
        # Time
        time_frame = ttk.Frame(frame)
        time_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            time_frame,
            text="Time:",
            font=('Helvetica', 10, 'bold')
        ).pack(side=tk.LEFT)
        
        time_text = self._format_event_time()
        ttk.Label(
            time_frame,
            text=time_text
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Location
        if self.event.location:
            loc_frame = ttk.Frame(frame)
            loc_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(
                loc_frame,
                text="Location:",
                font=('Helvetica', 10, 'bold')
            ).pack(side=tk.LEFT)
            
            ttk.Label(
                loc_frame,
                text=self.event.location,
                wraplength=280
            ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Description
        if self.event.description:
            desc_frame = ttk.Frame(frame)
            desc_frame.pack(fill=tk.BOTH, expand=True, pady=10)
            
            ttk.Label(
                desc_frame,
                text="Description:",
                font=('Helvetica', 10, 'bold')
            ).pack(anchor=tk.W)
            
            desc_text = tk.Text(
                desc_frame,
                wrap=tk.WORD,
                height=10,
                width=40,
                font=('Helvetica', 10)
            )
            desc_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
            desc_text.insert('1.0', self.event.description)
            desc_text.configure(state='disabled')
        
        # Close button
        ttk.Button(
            frame,
            text="Close",
            command=self.destroy
        ).pack(pady=10)
    
    def _format_event_time(self) -> str:
        """Format event time for display."""
        if self.event.is_all_day:
            return "All day"
        
        date_format = "%Y-%m-%d %H:%M"
        start = self.event.start_time.strftime(date_format)
        end = self.event.end_time.strftime(date_format)
        return f"{start} to {end}"

class SettingsDialog(tk.Toplevel):
    """Dialog for application settings."""
    
    def __init__(self, parent, config: CalendarConfig, on_save: callable):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save
        self.title("Settings")
        self.geometry("500x600")
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        
        # Center dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
    
    def _setup_ui(self) -> None:
        """Setup the settings UI."""
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Display settings
        display_frame = self._create_display_settings()
        notebook.add(display_frame, text="Display")
        
        # Notification settings
        notif_frame = self._create_notification_settings()
        notebook.add(notif_frame, text="Notifications")
        
        # Calendar sources
        sources_frame = self._create_calendar_sources()
        notebook.add(sources_frame, text="Calendars")
        
        # Save/Cancel buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            button_frame,
            text="Save",
            command=self._save_settings
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy
        ).pack(side=tk.RIGHT)
    
    def _create_display_settings(self) -> ttk.Frame:
        """Create display settings panel."""
        frame = ttk.Frame(self)
        frame.columnconfigure(1, weight=1)
        
        # View settings
        row = 0
        ttk.Label(
            frame,
            text="Default View:",
            font=('Helvetica', 10, 'bold')
        ).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.view_var = tk.StringVar(value=self.config.display.default_view)
        view_combo = ttk.Combobox(
            frame,
            textvariable=self.view_var,
            values=['day', 'week', 'month'],
            state='readonly'
        )
        view_combo.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Time format
        row += 1
        ttk.Label(
            frame,
            text="Time Format:",
            font=('Helvetica', 10, 'bold')
        ).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.time_format_var = tk.StringVar(value=self.config.display.time_format)
        time_combo = ttk.Combobox(
            frame,
            textvariable=self.time_format_var,
            values=['12h', '24h'],
            state='readonly'
        )
        time_combo.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Event visibility
        row += 1
        self.show_all_day_var = tk.BooleanVar(value=self.config.display.show_all_day_events)
        ttk.Checkbutton(
            frame,
            text="Show all-day events",
            variable=self.show_all_day_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        row += 1
        self.show_completed_var = tk.BooleanVar(value=self.config.display.show_completed_events)
        ttk.Checkbutton(
            frame,
            text="Show completed events",
            variable=self.show_completed_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        return frame
    
    def _create_notification_settings(self) -> ttk.Frame:
        """Create notification settings panel."""
        frame = ttk.Frame(self)
        frame.columnconfigure(1, weight=1)
        
        # Enable notifications
        row = 0
        self.notif_enabled_var = tk.BooleanVar(value=self.config.notifications.enabled)
        ttk.Checkbutton(
            frame,
            text="Enable notifications",
            variable=self.notif_enabled_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Sound notifications
        row += 1
        self.sound_enabled_var = tk.BooleanVar(value=self.config.notifications.sound_enabled)
        ttk.Checkbutton(
            frame,
            text="Enable notification sounds",
            variable=self.sound_enabled_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Default notification time
        row += 1
        ttk.Label(
            frame,
            text="Default Notification Time:",
            font=('Helvetica', 10, 'bold')
        ).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        
        default_minutes = int(self.config.notifications.default_time.total_seconds() / 60)
        self.default_time_var = tk.StringVar(value=str(default_minutes))
        time_entry = ttk.Entry(frame, textvariable=self.default_time_var, width=10)
        time_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(
            frame,
            text="minutes before event"
        ).grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
        
        return frame
    
    def _create_calendar_sources(self) -> ttk.Frame:
        """Create calendar sources panel."""
        frame = ttk.Frame(self)
        
        # Add new calendar button
        ttk.Button(
            frame,
            text="Add Calendar",
            command=self._add_calendar
        ).pack(anchor=tk.W, padx=5, pady=5)
        
        # Calendar list
        self.sources_frame = ttk.Frame(frame)
        self.sources_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self._refresh_calendar_list()
        
        return frame
    
    def _refresh_calendar_list(self) -> None:
        """Refresh the calendar sources list."""
        for widget in self.sources_frame.winfo_children():
            widget.destroy()
        
        for source_id, source in self.config.calendar_sources.items():
            source_frame = ttk.Frame(self.sources_frame)
            source_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(
                source_frame,
                text=source.name or source_id,
                foreground=source.color
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                source_frame,
                text="Edit",
                command=lambda sid=source_id: self._edit_calendar(sid)
            ).pack(side=tk.RIGHT, padx=2)
            
            ttk.Button(
                source_frame,
                text="Remove",
                command=lambda sid=source_id: self._remove_calendar(sid)
            ).pack(side=tk.RIGHT, padx=2)
    
    def _add_calendar(self) -> None:
        """Show dialog to add new calendar."""
        # Implementation for adding new calendar
        pass
    
    def _edit_calendar(self, source_id: str) -> None:
        """Show dialog to edit calendar."""
        # Implementation for editing calendar
        pass
    
    def _remove_calendar(self, source_id: str) -> None:
        """Remove calendar source."""
        if messagebox.askyesno("Remove Calendar", "Are you sure you want to remove this calendar?"):
            del self.config.calendar_sources[source_id]
            self._refresh_calendar_list()
    
    def _save_settings(self) -> None:
        """Save settings and close dialog."""
        try:
            # Update display settings
            self.config.display.default_view = self.view_var.get()
            self.config.display.time_format = self.time_format_var.get()
            self.config.display.show_all_day_events = self.show_all_day_var.get()
            self.config.display.show_completed_events = self.show_completed_var.get()
            
            # Update notification settings
            self.config.notifications.enabled = self.notif_enabled_var.get()
            self.config.notifications.sound_enabled = self.sound_enabled_var.get()
            try:
                minutes = int(self.default_time_var.get())
                self.config.notifications.default_time = timedelta(minutes=minutes)
            except ValueError:
                messagebox.showerror(
                    "Invalid Input",
                    "Default notification time must be a number of minutes"
                )
                return
            
            # Save and close
            self.on_save(self.config)
            self.destroy()
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            messagebox.showerror(
                "Error",
                "Failed to save settings. Please check the logs for details."
            )

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
        self._setup_keyboard_shortcuts()
        
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
    
    def _setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        self.bind('<Control-q>', lambda e: self.quit())
        self.bind('<Control-s>', lambda e: self._show_settings())
        self.bind('<Control-r>', lambda e: self._refresh_events())
        self.bind('<Control-t>', lambda e: self._go_to_today())
        self.bind('<Control-d>', lambda e: self._toggle_details())
        self.bind('<F5>', lambda e: self._refresh_events())
        
        # Accessibility shortcuts
        self.bind('<Control-plus>', lambda e: self._increase_font_size())
        self.bind('<Control-minus>', lambda e: self._decrease_font_size())
        self.bind('<Control-0>', lambda e: self._reset_font_size())
    
    def _setup_toolbar(self) -> None:
        """Setup the application toolbar."""
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
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
        
        # Refresh button
        ttk.Button(
            toolbar,
            text="Refresh",
            command=self._refresh_events
        ).pack(side="left", padx=20)
        
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
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.countdown_label = ttk.Label(
            status_bar,
            text="No upcoming events",
            font=('Helvetica', 10)
        )
        self.countdown_label.pack(side="left")
        
        # Add accessibility info
        self.status_message = ttk.Label(
            status_bar,
            text="Press F1 for keyboard shortcuts",
            font=('Helvetica', 10)
        )
        self.status_message.pack(side="right")
    
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
        if self.config.notifications.sound_enabled:
            self.notification_manager._play_notification_sound()
    
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
        SettingsDialog(self, self.config, self._save_settings)
    
    def _save_settings(self, new_config: CalendarConfig) -> None:
        """Save new configuration."""
        try:
            self.config = new_config
            self.config.save()
            
            # Apply settings
            self.calendar_viewer.set_show_all_day_events(new_config.display.show_all_day_events)
            self.calendar_viewer.set_show_completed_events(new_config.display.show_completed_events)
            self.calendar_grid.set_view_mode(new_config.display.default_view)
            
            # Refresh display
            self._refresh_events()
            
            messagebox.showinfo("Success", "Settings saved successfully")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            messagebox.showerror(
                "Error",
                "Failed to save settings. Please check the logs for details."
            )
    
    def _refresh_events(self) -> None:
        """Refresh calendar events."""
        try:
            # Get updated events from calendar viewer
            events = self.calendar_viewer.get_filtered_events()
            
            # Update calendar grid with new events
            self.calendar_grid.set_events(events)
            
            # Update countdown display
            self._update_countdown()
            
            logger.info("Successfully refreshed calendar events")
        except Exception as e:
            logger.error(f"Failed to refresh events: {e}")
            messagebox.showerror(
                "Error",
                "Failed to refresh calendar events. Please check the logs for details."
            )
    
    def _toggle_details(self) -> None:
        """Toggle event details panel."""
        selected_event = self.calendar_grid.selected_event
        if selected_event:
            EventDetailsDialog(self, selected_event)
    
    def _increase_font_size(self) -> None:
        """Increase application font size."""
        try:
            # Get current font sizes
            default_font = tk.font.nametofont("TkDefaultFont")
            text_font = tk.font.nametofont("TkTextFont") 
            fixed_font = tk.font.nametofont("TkFixedFont")
            
            # Increase sizes by 2
            default_font.configure(size=default_font.cget("size") + 2)
            text_font.configure(size=text_font.cget("size") + 2)
            fixed_font.configure(size=fixed_font.cget("size") + 2)
            
            # Update UI
            self.update_idletasks()
        except Exception as e:
            logger.error(f"Failed to increase font size: {e}")
    
    def _decrease_font_size(self) -> None:
        """Decrease application font size."""
        try:
            # Get current font sizes
            default_font = tk.font.nametofont("TkDefaultFont")
            text_font = tk.font.nametofont("TkTextFont")
            fixed_font = tk.font.nametofont("TkFixedFont")
            
            # Don't decrease below minimum size of 8
            new_size = max(8, default_font.cget("size") - 2)
            
            # Update fonts
            default_font.configure(size=new_size)
            text_font.configure(size=new_size)
            fixed_font.configure(size=new_size)
            
            # Update UI
            self.update_idletasks()
        except Exception as e:
            logger.error(f"Failed to decrease font size: {e}")
    
    def _reset_font_size(self) -> None:
        """Reset application font size."""
        try:
            # Reset to default sizes
            default_font = tk.font.nametofont("TkDefaultFont")
            text_font = tk.font.nametofont("TkTextFont")
            fixed_font = tk.font.nametofont("TkFixedFont")
            
            default_font.configure(size=10)  # Default system font size
            text_font.configure(size=10)
            fixed_font.configure(size=10)
            
            # Update UI
            self.update_idletasks()
        except Exception as e:
            logger.error(f"Failed to reset font size: {e}")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    config = CalendarConfig.load()
    
    # Start application
    app = CalendarApp(config)
    app.mainloop()