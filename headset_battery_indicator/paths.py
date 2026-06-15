"""
headset_battery_indicator.paths
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Filesystem locations for settings and logs.

The application runs in portable mode: settings and logs are stored next
to the executable (or the project root when run from source) instead of
the Windows registry or the user's home directory, so it leaves no trace
on the host system.
"""

import os
import sys


def get_app_dir() -> str:
    """Return the directory where settings and logs should be stored.

    When frozen by PyInstaller, this is the directory containing the
    executable. Otherwise, it's the project root (parent of this package).
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


APP_DIR = get_app_dir()
SETTINGS_FILE = os.path.join(APP_DIR, "settings.ini")
LOG_DIR = os.path.join(APP_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
