"""
headset_battery_indicator.paths
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Filesystem locations for settings and logs.

When running as a frozen Windows executable (the standalone .exe built
with PyInstaller), the app operates in portable mode: settings and logs
are stored next to the executable, so it can run from a USB drive without
leaving any trace on the host system.

On Linux, macOS, and when running from source (including Fedora/AUR
packages), settings and logs use the usual per-user locations:
QSettings' native format (e.g. ~/.config on Linux, the registry on
Windows) for settings, and ~/.local/share/HeadsetBatteryIndicator/logs
for logs.
"""

import os
import sys

PORTABLE = sys.platform == "win32" and getattr(sys, "frozen", False)

if PORTABLE:
    APP_DIR = os.path.dirname(sys.executable)
    SETTINGS_FILE = os.path.join(APP_DIR, "settings.ini")
    LOG_DIR = os.path.join(APP_DIR, "logs")
else:
    APP_DIR = None
    SETTINGS_FILE = None
    LOG_DIR = os.path.join(
        os.path.expanduser("~"),
        ".local", "share", "HeadsetBatteryIndicator", "logs",
    )

LOG_FILE = os.path.join(LOG_DIR, "app.log")
