#!/usr/bin/env python3

import sys
import subprocess
import re
import signal
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer

# --- Config ---
UPDATE_INTERVAL_MS = 60000  # 60 seconds

class HeadsetBatteryTray(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1. Setup tray menu (for quitting)
        self.menu = QMenu()
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        self.menu.addAction(quit_action)
        self.setContextMenu(self.menu)

        # 2. Setup update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(UPDATE_INTERVAL_MS)
        
        # 3. Run a first update to get an icon
        self.update_status()
        
        # 4. Show the icon
        self.setVisible(True)

    def get_battery_status(self):
        """Runs headsetcontrol and parses its output."""
        try:
            # Run command
            result = subprocess.run(
                ['headsetcontrol', '-b'],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
            
            # Parse output with regex
            level_match = re.search(r"Level:\s*(\d+%)", output)
            status_match = re.search(r"Status:\s*(BATTERY_CHARGING)", output)
            
            # Get device name (Parse from 2nd line, clean it up)
            name_match = re.search(r"^\s*(.*?)\s*\[0x.*\]\s*$", output.splitlines()[1], re.MULTILINE)
            
            if not level_match:
                # Error: Couldn't find battery level
                return {"status": "error", "error": "Parse Error"}

            # Extract data
            level_str = level_match.group(1)
            numeric_level = int(level_str.replace('%', ''))
            is_charging = (status_match is not None)
            
            # Assign name or a default
            device_name = name_match.group(1) if name_match else "Unknown Headset"
            
            return {
                "status": "ok",
                "level": numeric_level,
                "level_str": level_str,
                "is_charging": is_charging,
                "name": device_name
            }

        except (subprocess.CalledProcessError, FileNotFoundError):
            # Error (command failed or headset disconnected)
            return {"status": "error", "error": "Disconnected"}

    def update_status(self):
        """Updates the tray icon and tooltip."""
        
        data = self.get_battery_status()
        
        # Case 1: Disconnected or error
        if data["status"] == "error":
            self.setIcon(QIcon.fromTheme("audio-headset-symbolic"))
            self.setToolTip(f"Headset: {data['error']}")
            return

        # Case 2: Connected
        level = data["level"]
        level_str = data["level_str"]
        device_name = data["name"]
        icon_name = "battery-missing-symbolic" # Default icon
        
        if data["is_charging"]:
            icon_name = "battery-charging-symbolic"
            tooltip_status = f"Charging ({level_str})"
        else:
            tooltip_status = f"Discharging ({level_str})"
            # Set icon based on level
            if level > 90:
                icon_name = "battery-100-symbolic"
            elif level > 70:
                icon_name = "battery-080-symbolic"
            elif level > 50:
                icon_name = "battery-060-symbolic"
            elif level > 30:
                icon_name = "battery-040-symbolic"
            elif level > 10:
                icon_name = "battery-020-symbolic"
            else:
                icon_name = "battery-000-symbolic"

        # Apply the icon and tooltip
        self.setIcon(QIcon.fromTheme(icon_name))
        
        # Set the dynamic name in the tooltip
        self.setToolTip(f"{device_name}\nStatus: {tooltip_status}")


# --- Main execution block ---
if __name__ == "__main__":
    
    # Allow Ctrl+C (SIGINT) to quit the app
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Standard Qt app setup
    app = QApplication(sys.argv)
    
    # Don't quit when the last window is closed (we have none)
    app.setQuitOnLastWindowClosed(False)

    # Check if system tray is available
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("Error: System tray not available.")
        sys.exit(1)

    # Create and show our tray icon
    tray_icon = HeadsetBatteryTray()
    
    # Start the application loop
    sys.exit(app.exec())