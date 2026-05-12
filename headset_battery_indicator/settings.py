"""
headset_battery_indicator.settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Centralized application settings management.

This module provides the AppSettings class which acts as a single source of truth
for all application preferences, handling QSettings interaction transparently
and emitting signals when values change.
"""

import logging
import re
from typing import Optional

from PySide6.QtCore import QSettings, Signal, QObject

logger = logging.getLogger(__name__)

_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _is_valid_hex_color(value: str) -> bool:
    """Return True if *value* is a valid 6-digit HTML hex color (e.g. '#A1B2C3')."""
    return bool(_HEX_COLOR_RE.match(str(value)))


class AppSettings(QObject):
    """Centralized settings management with Qt Signal support.
    
    All application preferences are stored and retrieved through this class,
    ensuring consistency and making the app easier to test and maintain.
    
    Signals are emitted whenever a setting changes, allowing UI components
    to react without explicit method calls.
    """
    
    # Signals for settings changes
    notify_enabled_changed = Signal(bool)
    notify_threshold_changed = Signal(int)
    lights_enabled_changed = Signal(bool)
    sidetone_level_changed = Signal(int)
    chatmix_level_changed = Signal(int)
    inactive_time_changed = Signal(int)
    icon_fill_color_changed = Signal(str)
    icon_border_color_changed = Signal(str)
    icon_orientation_changed = Signal(str)
    icon_scale_changed = Signal(int)
    icon_show_text_changed = Signal(bool)
    poll_interval_changed = Signal(int)
    language_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings()
        self._load_all()

    def _load_all(self) -> None:
        """Load all settings from persistent storage into memory."""
        self._notify_enabled = self._settings.value("notifyEnabled", False, type=bool)
        self._notify_threshold = self._settings.value("notifyThreshold", 20, type=int)
        self._lights_on = self._settings.value("lightsOn", True, type=bool)
        self._sidetone_level = self._settings.value("sidetoneLevel", 0, type=int)
        self._chatmix_level = self._settings.value("chatmixLevel", 64, type=int)
        self._inactive_time = self._settings.value("inactiveTime", 0, type=int)
        self._icon_fill_color = self._settings.value("iconFillColor", "#00FF00", type=str)
        self._icon_border_color = self._settings.value("iconBorderColor", "#FFFFFF", type=str)
        self._icon_orientation = self._settings.value("iconOrientation", "Horizontal", type=str)
        self._icon_scale = self._settings.value("iconScale", 75, type=int)
        self._icon_show_text = self._settings.value("iconShowText", True, type=bool)
        self._poll_interval = self._settings.value("pollInterval", 60, type=int)
        self._language = self._settings.value("language", "system", type=str)

    # ==================== Notification Settings ====================

    @property
    def notify_enabled(self) -> bool:
        """Whether low battery notifications are enabled."""
        return self._notify_enabled

    @notify_enabled.setter
    def notify_enabled(self, value: bool) -> None:
        if self._notify_enabled != value:
            self._notify_enabled = value
            self._settings.setValue("notifyEnabled", value)
            self.notify_enabled_changed.emit(value)
            logger.debug(f"Setting changed: notifyEnabled={value}")

    @property
    def notify_threshold(self) -> int:
        """Battery percentage threshold for low-battery notifications (10-50%)."""
        return self._notify_threshold

    @notify_threshold.setter
    def notify_threshold(self, value: int) -> None:
        value = max(5, min(95, value))
        if self._notify_threshold != value:
            self._notify_threshold = value
            self._settings.setValue("notifyThreshold", value)
            self.notify_threshold_changed.emit(value)
            logger.debug(f"Setting changed: notifyThreshold={value}%")

    # ==================== Device Control Settings ====================

    @property
    def lights_enabled(self) -> bool:
        """Whether headset LEDs are enabled."""
        return self._lights_on

    @lights_enabled.setter
    def lights_enabled(self, value: bool) -> None:
        if self._lights_on != value:
            self._lights_on = value
            self._settings.setValue("lightsOn", value)
            self.lights_enabled_changed.emit(value)
            logger.debug(f"Setting changed: lightsOn={value}")

    @property
    def sidetone_level(self) -> int:
        """Microphone sidetone level (0-128)."""
        return self._sidetone_level

    @sidetone_level.setter
    def sidetone_level(self, value: int) -> None:
        value = max(0, min(128, value))
        if self._sidetone_level != value:
            self._sidetone_level = value
            self._settings.setValue("sidetoneLevel", value)
            self.sidetone_level_changed.emit(value)
            logger.debug(f"Setting changed: sidetoneLevel={value}")

    @property
    def chatmix_level(self) -> int:
        """Game/Chat mix level (0-128, where 0=game, 128=chat, 64=center)."""
        return self._chatmix_level

    @chatmix_level.setter
    def chatmix_level(self, value: int) -> None:
        value = max(0, min(128, value))
        if self._chatmix_level != value:
            self._chatmix_level = value
            self._settings.setValue("chatmixLevel", value)
            self.chatmix_level_changed.emit(value)
            logger.debug(f"Setting changed: chatmixLevel={value}")

    @property
    def inactive_time(self) -> int:
        """Auto power-off time in minutes (0=disabled, or 10/30/60/90)."""
        return self._inactive_time

    @inactive_time.setter
    def inactive_time(self, value: int) -> None:
        allowed = {0, 10, 30, 60, 90}
        if value not in allowed:
            logger.warning(f"Invalid inactiveTime: {value}, using 0")
            value = 0
        if self._inactive_time != value:
            self._inactive_time = value
            self._settings.setValue("inactiveTime", value)
            self.inactive_time_changed.emit(value)
            logger.debug(f"Setting changed: inactiveTime={value} minutes")

    # ==================== Icon/Visual Settings ====================

    @property
    def icon_fill_color(self) -> str:
        """Icon fill color as hex string (e.g., '#00FF00')."""
        return self._icon_fill_color

    @icon_fill_color.setter
    def icon_fill_color(self, value: str) -> None:
        if not _is_valid_hex_color(value):
            logger.warning(f"Invalid hex color ignored: iconFillColor={value!r}")
            return
        if self._icon_fill_color != value:
            self._icon_fill_color = value
            self._settings.setValue("iconFillColor", value)
            self.icon_fill_color_changed.emit(value)
            logger.debug(f"Setting changed: iconFillColor={value}")

    @property
    def icon_border_color(self) -> str:
        """Icon border color as hex string (e.g., '#FFFFFF')."""
        return self._icon_border_color

    @icon_border_color.setter
    def icon_border_color(self, value: str) -> None:
        if not _is_valid_hex_color(value):
            logger.warning(f"Invalid hex color ignored: iconBorderColor={value!r}")
            return
        if self._icon_border_color != value:
            self._icon_border_color = value
            self._settings.setValue("iconBorderColor", value)
            self.icon_border_color_changed.emit(value)
            logger.debug(f"Setting changed: iconBorderColor={value}")

    @property
    def icon_orientation(self) -> str:
        """Icon battery orientation: 'Horizontal' or 'Vertical'."""
        return self._icon_orientation

    @icon_orientation.setter
    def icon_orientation(self, value: str) -> None:
        if value not in ("Horizontal", "Vertical"):
            logger.warning(f"Invalid orientation: {value}, using Horizontal")
            value = "Horizontal"
        if self._icon_orientation != value:
            self._icon_orientation = value
            self._settings.setValue("iconOrientation", value)
            self.icon_orientation_changed.emit(value)
            logger.debug(f"Setting changed: iconOrientation={value}")

    @property
    def icon_scale(self) -> int:
        """Icon zoom/scale as percentage (50-150%)."""
        return self._icon_scale

    @icon_scale.setter
    def icon_scale(self, value: int) -> None:
        value = max(50, min(150, value))
        if self._icon_scale != value:
            self._icon_scale = value
            self._settings.setValue("iconScale", value)
            self.icon_scale_changed.emit(value)
            logger.debug(f"Setting changed: iconScale={value}%")

    @property
    def icon_show_text(self) -> bool:
        """Whether to show percentage/bolt inside the icon."""
        return self._icon_show_text

    @icon_show_text.setter
    def icon_show_text(self, value: bool) -> None:
        if self._icon_show_text != value:
            self._icon_show_text = value
            self._settings.setValue("iconShowText", value)
            self.icon_show_text_changed.emit(value)
            logger.debug(f"Setting changed: iconShowText={value}")

    # ==================== Polling ====================

    @property
    def poll_interval(self) -> int:
        """Battery polling interval in seconds (10-300)."""
        return self._poll_interval

    @poll_interval.setter
    def poll_interval(self, value: int) -> None:
        value = max(10, min(300, value))
        if self._poll_interval != value:
            self._poll_interval = value
            self._settings.setValue("pollInterval", value)
            self.poll_interval_changed.emit(value)
            logger.debug(f"Setting changed: pollInterval={value}s")

    # ==================== Language ====================

    @property
    def language(self) -> str:
        """Language code for UI translations: 'system', 'en', 'es', etc."""
        return self._language

    @language.setter
    def language(self, value: str) -> None:
        if self._language != value:
            self._language = value
            self._settings.setValue("language", value)
            self.language_changed.emit(value)
            logger.debug(f"Setting changed: language={value}")

    # ==================== Batch Operations ====================

    def get_all(self) -> dict:
        """Return all settings as a dictionary."""
        return {
            "notify_enabled": self._notify_enabled,
            "notify_threshold": self._notify_threshold,
            "lights_enabled": self._lights_on,
            "sidetone_level": self._sidetone_level,
            "chatmix_level": self._chatmix_level,
            "inactive_time": self._inactive_time,
            "icon_fill_color": self._icon_fill_color,
            "icon_border_color": self._icon_border_color,
            "icon_orientation": self._icon_orientation,
            "icon_scale": self._icon_scale,
            "icon_show_text": self._icon_show_text,
            "poll_interval": self._poll_interval,
        }

    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values."""
        logger.info("Resetting all settings to defaults")
        self.notify_enabled = False
        self.notify_threshold = 20
        self.lights_enabled = True
        self.sidetone_level = 0
        self.chatmix_level = 64
        self.inactive_time = 0
        self.icon_fill_color = "#00FF00"
        self.icon_border_color = "#FFFFFF"
        self.icon_orientation = "Horizontal"
        self.icon_scale = 75
        self.icon_show_text = True
        self.poll_interval = 60
