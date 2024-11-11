import logging
import sys
from pathlib import Path
from gui import CalendarApp
from config import CalendarConfig
import tkinter as tk

def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('calendar_app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Calendar Application")

    try:
        # Load configuration
        config = CalendarConfig.load()
        logger.info("Configuration loaded successfully")

        # Create and start GUI
        root = tk.Tk()
        root.title("Calendar Application")
        
        # Set application icon
        icon_path = Path(__file__).parent / 'assets' / 'icon.png'
        if icon_path.exists():
            try:
                root.iconphoto(True, tk.PhotoImage(file=str(icon_path)))
            except Exception as e:
                logger.warning(f"Failed to load application icon: {e}")

        app = CalendarApp(config)
        app.mainloop()

    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()