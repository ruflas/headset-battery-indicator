"""
headset_battery_indicator.tray
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
System tray icon for headset battery monitoring.

Handles device discovery, UI updates, device control commands,
low-battery notifications, and the optional debug REPL.
"""

import logging
import os
import shutil
import subprocess
import sys
import threading
from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QAction, QActionGroup, QDesktopServices
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .icon_renderer import BatteryIconRenderer
from .preferences_dialog import PreferencesDialog
from .settings import AppSettings
from .worker import BatteryWorker

logger = logging.getLogger(__name__)

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

LOG_DIR = os.path.join(
    os.path.expanduser("~"),
    ".local", "share", "HeadsetBatteryIndicator", "logs",
)
LOG_FILE = os.path.join(LOG_DIR, "app.log")


class HeadsetBatteryTray(QSystemTrayIcon):
    """System tray icon for headset battery monitoring.

    Displays battery percentage, handles device control commands,
    and manages low-battery notifications.
    """

    command_received = Signal(str)

    def __init__(
        self,
        app_settings: AppSettings,
        debug_mode: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.debug_mode = debug_mode
        self.use_test_device = False
        self.last_battery_data: Optional[Dict[str, Any]] = None
        self.notified_low_battery = False  # must be set before first update_status()
        self._worker: Optional[BatteryWorker] = None  # must be set before first update_status()
        self.app_settings = app_settings

        if debug_mode:
            _enable_console_logging()

        logger.info("Application starting up.")

        self.headsetcontrol_path: Optional[str] = self._find_headsetcontrol()

        self.icon_renderer = BatteryIconRenderer(
            fill_color=self.app_settings.icon_fill_color,
            border_color=self.app_settings.icon_border_color,
            orientation=self.app_settings.icon_orientation,
            scale=self.app_settings.icon_scale,
            show_text=self.app_settings.icon_show_text,
        )

        # Rebuild renderer whenever visual settings change
        self.app_settings.icon_fill_color_changed.connect(self._on_visual_settings_changed)
        self.app_settings.icon_border_color_changed.connect(self._on_visual_settings_changed)
        self.app_settings.icon_orientation_changed.connect(self._on_visual_settings_changed)
        self.app_settings.icon_scale_changed.connect(self._on_visual_settings_changed)
        self.app_settings.icon_show_text_changed.connect(self._on_visual_settings_changed)
        self.app_settings.poll_interval_changed.connect(self._on_poll_interval_changed)
        self.app_settings.notify_threshold_changed.connect(self._on_threshold_changed)

        if not self.headsetcontrol_path:
            logger.critical("HeadsetControl binary not found. Functionality disabled.")
            self.send_notification(
                self.tr("Dependency Error"),
                self.tr("HeadsetControl binary not found. Please install it."),
            )
            self.setToolTip(self.tr("ERROR: HeadsetControl not found."))

        # Defer startup commands so the tray icon appears immediately.
        # singleShot(0) fires on the first event-loop tick, after __init__ returns.
        QTimer.singleShot(0, self.apply_saved_settings)

        self._action_groups: list = []  # keeps QActionGroup Python refs alive (Bug C)
        self.menu = QMenu()
        self.setup_menu()
        self.setContextMenu(self.menu)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        if self.headsetcontrol_path:
            self.timer.start(self.app_settings.poll_interval * 1000)

        self.update_status()
        self.setVisible(True)

        if debug_mode:
            self._start_debug_console()

    # ------------------------------------------------------------------ #
    # Startup helpers
    # ------------------------------------------------------------------ #

    def _find_headsetcontrol(self) -> Optional[str]:
        """Search for the headsetcontrol binary in AppImage bundle then system PATH."""
        appdir = os.getenv("APPDIR")
        if appdir:
            bundled = os.path.join(appdir, "usr/bin/headsetcontrol")
            if os.path.exists(bundled):
                logger.info(f"Binary found in AppImage: {bundled}")
                return bundled

        path = shutil.which("headsetcontrol")
        if path:
            logger.info(f"Binary found in system PATH: {path}")
            return path

        logger.warning("HeadsetControl binary not found in AppImage or system PATH.")
        return None

    def _on_visual_settings_changed(self) -> None:
        """Recreate the icon renderer when any visual setting changes, then redraw."""
        self.icon_renderer = BatteryIconRenderer(
            fill_color=self.app_settings.icon_fill_color,
            border_color=self.app_settings.icon_border_color,
            orientation=self.app_settings.icon_orientation,
            scale=self.app_settings.icon_scale,
            show_text=self.app_settings.icon_show_text,
        )
        if self.last_battery_data:
            self.on_battery_result(self.last_battery_data)

    # ------------------------------------------------------------------ #
    # Menu construction
    # ------------------------------------------------------------------ #

    def setup_menu(self) -> None:
        """Build the right-click context menu."""

        # Info (read-only labels)
        self.info_name_action = QAction(self.tr("Device: ..."))
        self.info_name_action.setEnabled(False)
        self.menu.addAction(self.info_name_action)

        self.info_status_action = QAction(self.tr("Status: ..."))
        self.info_status_action.setEnabled(False)
        self.menu.addAction(self.info_status_action)
        self.menu.addSeparator()

        # Preferences
        pref_action = QAction(self.tr("Preferences..."), self)
        pref_action.triggered.connect(self.open_preferences)
        self.menu.addAction(pref_action)

        # Notifications
        self.notify_action = QAction(self.tr("Notify on low battery"), self)
        self.notify_action.setCheckable(True)
        self.notify_action.setChecked(self.app_settings.notify_enabled)
        self.notify_action.toggled.connect(self.on_notify_toggled)
        self.menu.addAction(self.notify_action)

        # Device controls
        self.menu.addSeparator()

        self.lights_action = QAction(self.tr("Enable Headset Lights"), self)
        self.lights_action.setCheckable(True)
        self.lights_action.setChecked(self.app_settings.lights_enabled)
        self.lights_action.toggled.connect(self.on_lights_toggled)
        self.menu.addAction(self.lights_action)

        self.sidetone_menu = self._make_level_menu(
            self.tr("Set Sidetone Level"),
            {
                self.tr("Off"): 0,
                self.tr("Low"): 32,
                self.tr("Medium"): 64,
                self.tr("High"): 96,
                self.tr("Max"): 128,
            },
            self.app_settings.sidetone_level,
            self.on_sidetone_changed,
        )
        self.menu.addMenu(self.sidetone_menu)

        self.chatmix_menu = self._make_level_menu(
            self.tr("Set ChatMix Level"),
            {
                self.tr("Game Max (0)"): 0,
                self.tr("Game Bias (32)"): 32,
                self.tr("Center (64)"): 64,
                self.tr("Chat Bias (96)"): 96,
                self.tr("Chat Max (128)"): 128,
            },
            self.app_settings.chatmix_level,
            self.on_chatmix_changed,
        )
        self.menu.addMenu(self.chatmix_menu)

        self.inactivetime_menu = self._make_level_menu(
            self.tr("Set Auto-Off Time (Min)"),
            {
                self.tr("Disabled (0)"): 0,
                self.tr("10 min"): 10,
                self.tr("30 min"): 30,
                self.tr("60 min"): 60,
                self.tr("90 min"): 90,
            },
            self.app_settings.inactive_time,
            self.on_inactivetime_changed,
        )
        self.menu.addMenu(self.inactivetime_menu)

        # Debug tools (only in debug mode)
        if self.debug_mode:
            self.menu.addSeparator()
            debug_menu = QMenu(self.tr("Debug & Logs"), self.menu)
            action_show = QAction(self.tr("Show Log Folder"), self.menu)
            action_show.triggered.connect(self.open_log_folder)
            debug_menu.addAction(action_show)
            action_clear = QAction(self.tr("Clear Log File"), self)
            action_clear.triggered.connect(self.clear_log_file)
            debug_menu.addAction(action_clear)
            self.menu.addMenu(debug_menu)

        # Footer actions
        refresh_action = QAction(self.tr("🔄 Update Status Now"), self)
        refresh_action.triggered.connect(self.update_status)
        self.menu.addAction(refresh_action)

        self.menu.addSeparator()
        quit_action = QAction(self.tr("Exit"), self)
        quit_action.triggered.connect(QApplication.instance().quit)
        self.menu.addAction(quit_action)

    def _make_level_menu(
        self,
        title: str,
        options: Dict[str, int],
        current_value: int,
        slot: Callable[[QAction], None],
    ) -> QMenu:
        """Build a submenu with an exclusive group of checkable actions."""
        menu = QMenu(title)
        group = QActionGroup(self)
        group.setExclusive(True)
        for text, value in options.items():
            action = QAction(text, self)
            action.setCheckable(True)
            action.setData(value)
            action.setChecked(value == current_value)
            menu.addAction(action)
            group.addAction(action)
        group.triggered.connect(slot)
        self._action_groups.append(group)  # prevent Python GC from dropping the wrapper
        return menu

    # ------------------------------------------------------------------ #
    # Preferences
    # ------------------------------------------------------------------ #

    def open_preferences(self) -> None:
        dlg = PreferencesDialog(self.app_settings, None)
        dlg.settings_saved.connect(self._on_prefs_saved)
        dlg.exec()

    def _on_prefs_saved(self) -> None:
        if self.last_battery_data:
            self.on_battery_result(self.last_battery_data)
        else:
            self.update_status()

    # ------------------------------------------------------------------ #
    # Log utilities (debug mode)
    # ------------------------------------------------------------------ #

    def open_log_folder(self) -> None:
        os.makedirs(LOG_DIR, exist_ok=True)
        logger.info(f"Opening log folder: {LOG_DIR}")
        QDesktopServices.openUrl(QUrl.fromLocalFile(LOG_DIR))

    def clear_log_file(self) -> None:
        try:
            with open(LOG_FILE, "w") as f:
                f.truncate(0)
            logger.info("Log file cleared.")
            self.send_notification(self.tr("Logs"), self.tr("Log file cleared successfully."))
        except OSError as e:
            logger.error(f"Failed to clear log file: {e}")
            self.send_notification(self.tr("Error"), self.tr("Could not clear log file."))

    # ------------------------------------------------------------------ #
    # Device commands
    # ------------------------------------------------------------------ #

    def run_headset_command(self, args_list: list) -> None:
        """Run a headsetcontrol command. No-op if the binary is missing."""
        if not self.headsetcontrol_path:
            logger.warning("Attempted command but headsetcontrol binary is missing.")
            return

        command = [self.headsetcontrol_path]
        if self.use_test_device:
            command.extend(["--test-device", "[0xf00b:0xa00c]"])
        command.extend(args_list)

        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=CREATE_NO_WINDOW,
            )
            logger.info(f"Ran command: {' '.join(command)}")
        except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired) as e:
            logger.error(f"Command failed: {' '.join(command)} — {e}")
            self.send_notification(
                self.tr("Headset Command Failed"),
                self.tr("Failed to run: {}\nIs it connected? Check logs.").format(" ".join(command)),
            )

    def apply_saved_settings(self) -> None:
        """Apply all persisted settings to the headset at startup."""
        if not self.headsetcontrol_path:
            logger.info("Skipping startup settings: binary not found.")
            return

        logger.info("Applying saved settings on startup.")
        self.run_headset_command(["-l", "1" if self.app_settings.lights_enabled else "0"])
        self.run_headset_command(["-s", str(self.app_settings.sidetone_level)])
        self.run_headset_command(["-m", str(self.app_settings.chatmix_level)])
        self.run_headset_command(["-i", str(self.app_settings.inactive_time)])
        logger.info(
            f"Startup settings applied: "
            f"Lights={self.app_settings.lights_enabled}, "
            f"Sidetone={self.app_settings.sidetone_level}, "
            f"ChatMix={self.app_settings.chatmix_level}, "
            f"AutoOff={self.app_settings.inactive_time}m"
        )

    # ------------------------------------------------------------------ #
    # Menu callbacks
    # ------------------------------------------------------------------ #

    def on_notify_toggled(self, checked: bool) -> None:
        self.app_settings.notify_enabled = checked
        self.notified_low_battery = False
        logger.info(f"Notifications: {checked}")

    def _on_threshold_changed(self, value: int) -> None:
        self.notified_low_battery = False
        logger.info(f"Notification threshold changed: {value}%")

    def _on_poll_interval_changed(self, seconds: int) -> None:
        if self.timer.isActive():
            self.timer.start(seconds * 1000)
        logger.info(f"Poll interval changed: {seconds}s")

    def on_lights_toggled(self, checked: bool) -> None:
        self.app_settings.lights_enabled = checked
        self.run_headset_command(["-l", "1" if checked else "0"])
        logger.info(f"Lights: {'ON' if checked else 'OFF'}")

    def on_sidetone_changed(self, action: QAction) -> None:
        level = action.data()
        self.app_settings.sidetone_level = level
        self.run_headset_command(["-s", str(level)])
        logger.info(f"Sidetone: {level}")

    def on_chatmix_changed(self, action: QAction) -> None:
        level = action.data()
        self.app_settings.chatmix_level = level
        self.run_headset_command(["-m", str(level)])
        logger.info(f"ChatMix: {level}")

    def on_inactivetime_changed(self, action: QAction) -> None:
        minutes = action.data()
        self.app_settings.inactive_time = minutes
        self.run_headset_command(["-i", str(minutes)])
        logger.info(f"Auto-Off: {minutes} min")

    # ------------------------------------------------------------------ #
    # Core update loop
    # ------------------------------------------------------------------ #

    def send_notification(self, title: str, message: str) -> None:
        self.showMessage(title, message, QSystemTrayIcon.Information, 10_000)

    def update_status(self) -> None:
        """Start a background worker to query headsetcontrol.

        Skips if the previous worker is still running to avoid overlapping
        threads and out-of-order signal delivery.
        """
        if self._worker is not None and self._worker.isRunning():
            logger.debug("update_status: previous worker still running, skipping.")
            return

        self._worker = BatteryWorker(self.headsetcontrol_path, self.use_test_device)
        self._worker.status_received.connect(self.on_battery_result)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_worker_finished(self) -> None:
        """Clear the worker reference and schedule C++ object deletion.

        Must null out self._worker BEFORE deleteLater so the next
        update_status call never touches a dead C++ wrapper.
        """
        worker, self._worker = self._worker, None
        if worker is not None:
            worker.deleteLater()

    @Slot(dict)
    def on_battery_result(self, data: Dict[str, Any]) -> None:
        """Receive parsed battery data from the worker and update all UI elements."""
        self.last_battery_data = data

        if data["status"] == "unavailable":
            style = self.app_settings.disconnected_style
            if style == "hide":
                self.setVisible(False)
            else:
                self.setVisible(True)
                if style == "error":
                    self.setIcon(self.icon_renderer.render(0, False, error=True))
                else:
                    self.setIcon(self.icon_renderer.render(0, False))
            self.setToolTip(self.tr("Headset: Powered Off"))
            self.info_name_action.setText(self.tr("Headset"))
            self.info_status_action.setText(self.tr("Status: Powered Off"))
            self.notified_low_battery = False
            return

        if data["status"] == "error":
            self.setIcon(self.icon_renderer.render(0, False, error=True))
            if data.get("error") != "Binary Missing":
                self.setToolTip(self.tr("Headset: {}").format(data["error"]))
                self.info_name_action.setText(self.tr("Headset"))
                self.info_status_action.setText(self.tr("Status: {}").format(data["error"]))
            self.notified_low_battery = False
            return

        level: int = data["level"]
        level_str: str = data["level_str"]
        device_name: str = data["name"]
        is_charging: bool = data["is_charging"]

        self.setVisible(True)
        self.setIcon(self.icon_renderer.render(level, is_charging))

        if (
            self.app_settings.notify_enabled
            and level <= self.app_settings.notify_threshold
            and not is_charging
        ):
            if not self.notified_low_battery:
                logger.warning(f"Low battery threshold reached: {level_str}")
                self.send_notification(
                    self.tr("Low Headset Battery"),
                    self.tr("{} is at {}.").format(device_name, level_str),
                )
                self.run_headset_command(["-n", "1"])
                self.notified_low_battery = True
        elif level > self.app_settings.notify_threshold:
            self.notified_low_battery = False

        charge_str = self.tr("Charging ({})") if is_charging else self.tr("Discharging ({})")
        tooltip_status = charge_str.format(level_str)
        self.setToolTip("{}\n{}".format(device_name, self.tr("Status: {}").format(tooltip_status)))
        self.info_name_action.setText(device_name)
        self.info_status_action.setText(self.tr("Status: {}").format(tooltip_status))

    # ------------------------------------------------------------------ #
    # Debug REPL
    # ------------------------------------------------------------------ #

    def _start_debug_console(self) -> None:
        print("--- Headset Indicator DEBUG MODE ---")
        print(f"Log file: {LOG_FILE}")
        print("Commands:")
        print("  log-test                    write sample log entries")
        print("  setIcon <n> [charging]      test icon at percentage n")
        print("  setIcon error               test error icon")
        print("  notification                send test desktop notification")
        print("  update                      force single status update")
        print("  resume                      restart automatic updates")
        print("  mockon / mockoff            enable / disable test device")
        print("  exit                        quit the application")
        print("------------------------------------")

        self.command_received.connect(self.handle_debug_command)

        def _read_stdin() -> None:
            while True:
                try:
                    line = sys.stdin.readline()
                    if line:
                        self.command_received.emit(line.strip())
                except ValueError:
                    break

        threading.Thread(target=_read_stdin, daemon=True).start()

    @Slot(str)
    def handle_debug_command(self, line: str) -> None:
        """Process a command received from the debug console thread."""
        if not line:
            return
        parts = line.split()
        command = parts[0].lower()

        try:
            if command == "log-test":
                logger.debug("DEBUG message (file only)")
                logger.info("INFO message")
                logger.warning("WARNING message")
                logger.error("ERROR message")
                logger.critical("CRITICAL message")

            elif command == "seticon":
                if len(parts) < 2:
                    print("Usage: setIcon <number> [charging] | error")
                    return
                self.timer.stop()
                print("Automatic updates paused. Type 'resume' to restart.")
                arg = parts[1].lower()
                if arg == "error":
                    self.setIcon(self.icon_renderer.render(0, False, error=True))
                elif arg.isdigit():
                    lvl = int(arg)
                    charging = len(parts) > 2 and parts[2].lower() == "charging"
                    self.setIcon(self.icon_renderer.render(lvl, charging))
                else:
                    print("Usage: setIcon <number> [charging] | error")

            elif command == "notification":
                self.send_notification("Debug Notification", "This is a test message.")
                self.run_headset_command(["-n", "1"])

            elif command == "update":
                self.update_status()
                QApplication.processEvents()

            elif command in ("mock", "mockon", "mockoff"):
                if command == "mockon":
                    self.use_test_device = True
                elif command == "mockoff":
                    self.use_test_device = False
                else:
                    self.use_test_device = len(parts) > 1 and parts[1].lower() == "on"
                print(f"Test Device Mode: {'ON' if self.use_test_device else 'OFF'}")
                self.update_status()

            elif command == "resume":
                self.timer.start(self.app_settings.poll_interval * 1000)
                self.update_status()
                QApplication.processEvents()

            elif command == "exit":
                logger.info("Application exiting via debug command.")
                QApplication.instance().quit()

            else:
                print(f"Unknown command: {command!r}")

        except Exception as e:
            logger.critical(f"Unhandled exception in debug handler: {e}")


# ------------------------------------------------------------------ #
# Package-level logging helpers
# ------------------------------------------------------------------ #

def _enable_console_logging() -> None:
    """Attach a stdout handler to the package logger for debug output.

    Safe to call multiple times — adds the handler at most once.
    """
    pkg_logger = logging.getLogger("headset_battery_indicator")
    if any(
        isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) is sys.stdout
        for h in pkg_logger.handlers
    ):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    pkg_logger.addHandler(handler)
