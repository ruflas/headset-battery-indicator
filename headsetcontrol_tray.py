#!/usr/bin/env python3

import sys
import subprocess
import re
import signal
import textwrap  # To format the help text
from PySide6.QtCore import QTimer, QSettings, QSocketNotifier
from PySide6.QtGui import QIcon, QAction, QActionGroup
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

# --- Config ---
UPDATE_INTERVAL_MS = 60000  # 60 seconds

class HeadsetBatteryTray(QSystemTrayIcon):
    def __init__(self, debug_mode=False, parent=None):
        super().__init__(parent)
        
        self.settings = QSettings()
        self.load_settings()

        self.menu = QMenu()
        self.setup_menu()
        self.setContextMenu(self.menu)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(UPDATE_INTERVAL_MS)
        
        self.update_status()
        self.setVisible(True)
        
        if debug_mode:
            print("--- Headset Indicator DEBUG MODE ---")
            print("Type commands and press Enter:")
            print("  setIcon [icon-name]  (e.g., 'battery-100-symbolic')")
            print("  notification         (sends desktop + headset sound)")
            print("  update               (forces a status update)")
            print("  resume               (resumes automatic updates)")
            print("  exit                 (quits the application)")
            print("------------------------------------")
            
            self.stdin_notifier = QSocketNotifier(sys.stdin.fileno(), QSocketNotifier.Type.Read, self)
            self.stdin_notifier.activated.connect(self.handle_debug_command)

    def load_settings(self):
        """Loads user settings from QSettings."""
        self.notify_enabled = self.settings.value("notifyEnabled", False, type=bool)
        self.notify_threshold = self.settings.value("notifyThreshold", 20, type=int)
        self.notified_low_battery = False

    def setup_menu(self):
        """Builds the context (right-click) menu."""
        self.info_name_action = QAction("Device: ...")
        self.info_name_action.setEnabled(False)
        self.menu.addAction(self.info_name_action)

        self.info_status_action = QAction("Status: ...")
        self.info_status_action.setEnabled(False)
        self.menu.addAction(self.info_status_action)
        self.menu.addSeparator()

        self.notify_action = QAction("Notify on low battery", self)
        self.notify_action.setCheckable(True)
        self.notify_action.setChecked(self.notify_enabled)
        self.notify_action.toggled.connect(self.on_notify_toggled)
        self.menu.addAction(self.notify_action)

        self.threshold_menu = QMenu("Set Notification Level")
        self.threshold_group = QActionGroup(self)
        self.threshold_group.setExclusive(True)
        
        threshold_levels = [10, 20, 30, 40, 50]
        for level in threshold_levels:
            action = QAction(f"{level}%", self)
            action.setCheckable(True)
            action.setData(level)
            if level == self.notify_threshold:
                action.setChecked(True)
            self.threshold_menu.addAction(action)
            self.threshold_group.addAction(action)

        self.threshold_group.triggered.connect(self.on_threshold_changed)
        self.menu.addMenu(self.threshold_menu)
        self.menu.addSeparator()

        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        self.menu.addAction(quit_action)

    def handle_debug_command(self):
        """Processes commands from stdin in debug mode."""
        try:
            line = sys.stdin.readline().strip()
            if not line:
                return
            
            parts = line.split()
            if not parts:
                return
            
            command = parts[0].lower()
            
            if command == "seticon":
                if len(parts) > 1:
                    icon_name = parts[1]
                    print(f"Debug: Setting icon to '{icon_name}'.")
                    self.timer.stop() 
                    print("Debug: Automatic updates paused. Type 'resume' to restart.")
                    self.setIcon(QIcon.fromTheme(icon_name))
                    QApplication.processEvents()
                else:
                    print("Debug Error: 'setIcon' requires an icon name.")
            
            elif command == "notification":
                print("Debug: Sending test notification...")
                self.send_notification("Debug Notification", "This is a test message.")
                try:
                    print("Debug: Playing notification sound on headset ('headsetcontrol -n 1')...")
                    subprocess.run(['headsetcontrol', '-n', '1'], check=True, capture_output=True)
                except Exception as e:
                    print(f"Debug Error: Failed to run 'headsetcontrol -n 1': {e}")
            
            elif command == "update":
                print("Debug: Forcing single status update...")
                self.update_status()
                QApplication.processEvents()

            elif command == "resume":
                print("Debug: Resuming automatic updates...")
                self.timer.start(UPDATE_INTERVAL_MS)
                self.update_status()
                QApplication.processEvents()

            elif command == "exit":
                print("Debug: Exiting...")
                QApplication.instance().quit()

            else:
                print(f"Debug Error: Unknown command '{command}'")

        except Exception as e:
            print(f"Debug Error: {e}")

    def on_notify_toggled(self, checked):
        """Called when the user toggles notifications."""
        self.notify_enabled = checked
        self.settings.setValue("notifyEnabled", self.notify_enabled)
        self.notified_low_battery = False 

    def on_threshold_changed(self, action):
        """Called when the user changes the threshold."""
        self.notify_threshold = action.data()
        self.settings.setValue("notifyThreshold", self.notify_threshold)
        self.notified_low_battery = False

    def send_notification(self, title, message):
        """Sends a desktop notification."""
        icon = QIcon.fromTheme("battery-caution-symbolic")
        self.showMessage(title, message, icon, 10000)

    def get_battery_status(self):
        """Runs headsetcontrol and parses its output."""
        try:
            result = subprocess.run(
                ['headsetcontrol', '-b'],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
            
            level_match = re.search(r"Level:\s*(\d+%)", output)
            status_match = re.search(r"Status:\s*(BATTERY_CHARGING)", output)
            name_match = re.search(r"^\s*(.*?)\s*\[0x.*\]\s*$", output.splitlines()[1], re.MULTILINE)
            
            if not level_match:
                return {"status": "error", "error": "Parse Error"}

            level_str = level_match.group(1)
            numeric_level = int(level_str.replace('%', ''))
            is_charging = (status_match is not None)
            device_name = name_match.group(1) if name_match else "Unknown Headset"
            
            return {
                "status": "ok",
                "level": numeric_level,
                "level_str": level_str,
                "is_charging": is_charging,
                "name": device_name
            }

        except (subprocess.CalledProcessError, FileNotFoundError):
            return {"status": "error", "error": "Disconnected"}

    def update_status(self):
        """Updates the icon, tooltip and checks for notification logic."""
        
        data = self.get_battery_status()
        
        if data["status"] == "error":
            self.setIcon(QIcon.fromTheme("audio-headset-symbolic"))
            self.setToolTip(f"Headset: {data['error']}")
            self.info_name_action.setText("Headset")
            self.info_status_action.setText(f"Status: {data['error']}")
            self.notified_low_battery = False
            return

        level = data["level"]
        level_str = data["level_str"]
        device_name = data["name"]
        icon_name = "battery-missing-symbolic"
        
        if data["is_charging"]:
            icon_name = "battery-charging-symbolic"
            tooltip_status = f"Charging ({level_str})"
            self.notified_low_battery = False
        else:
            tooltip_status = f"Discharging ({level_str})"
            if level > 90: icon_name = "battery-100-symbolic"
            elif level > 70: icon_name = "battery-080-symbolic"
            elif level > 50: icon_name = "battery-060-symbolic"
            elif level > 30: icon_name = "battery-040-symbolic"
            elif level > 10: icon_name = "battery-020-symbolic"
            else: icon_name = "battery-000-symbolic"

            if self.notify_enabled and level <= self.notify_threshold:
                if not self.notified_low_battery:
                    self.send_notification(
                        "Low Headset Battery",
                        f"{device_name} is at {level_str}."
                    )
                    try:
                        subprocess.run(['headsetcontrol', '-n', '1'], check=True, capture_output=True)
                    except Exception as e:
                        print(f"Error playing headset notification: {e}")
                    self.notified_low_battery = True
            
            elif level > self.notify_threshold:
                self.notified_low_battery = False

        self.setIcon(QIcon.fromTheme(icon_name))
        self.setToolTip(f"{device_name}\nStatus: {tooltip_status}")
        
        self.info_name_action.setText(device_name)
        self.info_status_action.setText(f"Status: {tooltip_status}")

# --- Main execution block ---
if __name__ == "__main__":
    
    # --- NEW: -h / --help Check ---
    if "-h" in sys.argv or "--help" in sys.argv:
        # textwrap.dedent removes leading whitespace from the block
        HELP_TEXT = textwrap.dedent("""
        Headset Battery Indicator
        
        A system tray icon to monitor headset battery levels,
        based on HeadsetControl.
        
        Usage:
          python3 headsetcontrol_tray.py [options]
        
        Options:
          -h, --help    Show this help message and exit.
          -debug        Run in debug mode, allowing interactive commands
                        (e.g., 'notification', 'setIcon [name]').
        
        This script is a frontend and requires 'headsetcontrol' to be installed.
        """)
        print(HELP_TEXT)
        sys.exit(0)  # Exit cleanly
    # --- END NEW BLOCK ---

    debug_mode = "-debug" in sys.argv
    
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    
    app.setOrganizationName("MyScripts")
    app.setApplicationName("HeadsetBatteryIndicator")

    app.setQuitOnLastWindowClosed(False)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("Error: System tray not available.")
        sys.exit(1)

    tray_icon = HeadsetBatteryTray(debug_mode=debug_mode)
    
    sys.exit(app.exec())
