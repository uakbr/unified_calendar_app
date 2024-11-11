#!/usr/bin/env python3
"""
Privacy Calendar Application
A unified calendar application that aggregates multiple calendar sources
and provides customizable notifications.
"""

import logging
import sys
from pathlib import Path
import tkinter as tk
from gui import CalendarApp
from config import CalendarConfig, ConfigError
import argparse

def setup_logging(log_level: str = "INFO") -> None:
    """Configure application logging."""
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    logging.basicConfig(
        level=log_levels.get(log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('calendar_app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Privacy Calendar Application")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.json"),
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level"
    )
    return parser.parse_args()

def main() -> None:
    """Main application entry point."""
    args = parse_arguments()
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Calendar Application")
        
        # Load configuration
        config = CalendarConfig.load(args.config)
        logger.info("Configuration loaded successfully")
        
        # Create and start GUI
        root = tk.Tk()
        root.title("Privacy Calendar")
        
        # Set application icon
        icon_path = Path(__file__).parent / "assets" / "icon.png"
        if icon_path.exists():
            try:
                icon_image = tk.PhotoImage(file=str(icon_path))
                root.iconphoto(True, icon_image)
            except Exception as e:
                logger.warning(f"Failed to load application icon: {e}")
        
        # Configure window
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = min(1024, screen_width - 100)
        window_height = min(768, screen_height - 100)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Create application instance
        app = CalendarApp(config)
        
        # Handle window close
        def on_closing():
            try:
                app.shutdown()
                root.destroy()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
                sys.exit(1)
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start application
        app.mainloop()
        
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        tk.messagebox.showerror("Configuration Error", str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        tk.messagebox.showerror("Error", f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()