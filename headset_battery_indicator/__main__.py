#!/usr/bin/env python3

import logging
import os
import signal
import sys
import textwrap
from logging.handlers import RotatingFileHandler

from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from .i18n import install_translator
from .settings import AppSettings
from .tray import HeadsetBatteryTray, LOG_DIR, LOG_FILE

_MAX_LOG_BYTES = 10 * 1024 * 1024  # 10 MB
_BACKUP_COUNT = 1


def setup_logging() -> None:
    """Configure a rotating file logger for the entire headset_battery_indicator package.

    Attaches the handler to the package-level logger so all sub-modules
    (tray, worker, parsing, settings, icon_renderer) write to the same file.
    Safe to call multiple times — adds the handler at most once.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    pkg_logger = logging.getLogger("headset_battery_indicator")
    pkg_logger.setLevel(logging.DEBUG)

    if any(isinstance(h, RotatingFileHandler) for h in pkg_logger.handlers):
        return  # already configured

    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=_MAX_LOG_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    )
    pkg_logger.addHandler(handler)


def main() -> None:
    """Entry point for the headset battery indicator application."""
    if "-h" in sys.argv or "--help" in sys.argv:
        print(textwrap.dedent("""
            Headset Battery Indicator

            A system tray icon to monitor headset battery levels,
            based on HeadsetControl.

            Usage:
              headset-battery-indicator [options]

            Options:
              -h, --help    Show this help message and exit.
              -debug        Run in debug mode with interactive console commands.

            Requires 'headsetcontrol' to be installed on the system.
        """).strip())
        sys.exit(0)

    debug_mode = "-debug" in sys.argv

    setup_logging()

    # Allow Ctrl-C to terminate the Qt event loop cleanly
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setOrganizationName("MyScripts")
    app.setApplicationName("HeadsetBatteryIndicator")
    app.setQuitOnLastWindowClosed(False)

    app_settings = AppSettings()
    install_translator(app, app_settings.language)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        logging.getLogger(__name__).critical("System tray not available. Exiting.")
        print("Error: System tray not available.")
        sys.exit(1)

    HeadsetBatteryTray(app_settings, debug_mode=debug_mode, parent=app)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
