"""
tests.test_settings
~~~~~~~~~~~~~~~~~~~
Unit tests for AppSettings: defaults, validation, signal emission,
persistence contract, and batch operations.

Requires pytest-qt (pip install pytest-qt) so that a QApplication is
available for QObject/signal usage.  QSettings is redirected to a
per-test INI file via monkeypatch so real user settings are never touched.
"""

from headset_battery_indicator.settings import AppSettings


# ---------------------------------------------------------------------------
# Default values  (settings fixture provided by conftest.py)
# ---------------------------------------------------------------------------

class TestDefaults:
    def test_notify_enabled(self, settings):
        assert settings.notify_enabled is False

    def test_notify_threshold(self, settings):
        assert settings.notify_threshold == 20

    def test_lights_enabled(self, settings):
        assert settings.lights_enabled is True

    def test_sidetone_level(self, settings):
        assert settings.sidetone_level == 0

    def test_chatmix_level(self, settings):
        assert settings.chatmix_level == 64

    def test_inactive_time(self, settings):
        assert settings.inactive_time == 0

    def test_icon_fill_color(self, settings):
        assert settings.icon_fill_color == "#00FF00"

    def test_icon_border_color(self, settings):
        assert settings.icon_border_color == "#FFFFFF"

    def test_icon_orientation(self, settings):
        assert settings.icon_orientation == "Horizontal"

    def test_icon_scale(self, settings):
        assert settings.icon_scale == 75

    def test_icon_show_text(self, settings):
        assert settings.icon_show_text is True


# ---------------------------------------------------------------------------
# Range / value validation (clamping and whitelisting)
# ---------------------------------------------------------------------------

class TestValidation:
    def test_sidetone_clamps_above_max(self, settings):
        settings.sidetone_level = 999
        assert settings.sidetone_level == 128

    def test_sidetone_clamps_below_min(self, settings):
        settings.sidetone_level = -1
        assert settings.sidetone_level == 0

    def test_sidetone_boundary_zero(self, settings):
        settings.sidetone_level = 0
        assert settings.sidetone_level == 0

    def test_sidetone_boundary_128(self, settings):
        settings.sidetone_level = 128
        assert settings.sidetone_level == 128

    def test_chatmix_clamps_above(self, settings):
        settings.chatmix_level = 200
        assert settings.chatmix_level == 128

    def test_chatmix_clamps_below(self, settings):
        settings.chatmix_level = -5
        assert settings.chatmix_level == 0

    def test_notify_threshold_clamps_above(self, settings):
        settings.notify_threshold = 100
        assert settings.notify_threshold == 95

    def test_notify_threshold_clamps_below(self, settings):
        settings.notify_threshold = 0
        assert settings.notify_threshold == 5

    def test_icon_scale_clamps_above(self, settings):
        settings.icon_scale = 999
        assert settings.icon_scale == 150

    def test_icon_scale_clamps_below(self, settings):
        settings.icon_scale = 1
        assert settings.icon_scale == 50

    def test_inactive_time_rejects_invalid_value(self, settings):
        settings.inactive_time = 45  # not in {0,10,30,60,90}
        assert settings.inactive_time == 0

    def test_inactive_time_accepts_all_valid_values(self, settings):
        for valid in (0, 10, 30, 60, 90):
            settings.inactive_time = valid
            assert settings.inactive_time == valid

    def test_icon_orientation_rejects_invalid(self, settings):
        settings.icon_orientation = "Diagonal"
        assert settings.icon_orientation == "Horizontal"

    def test_icon_orientation_accepts_vertical(self, settings):
        settings.icon_orientation = "Vertical"
        assert settings.icon_orientation == "Vertical"


# ---------------------------------------------------------------------------
# Signal emission
# ---------------------------------------------------------------------------

class TestSignals:
    def _collect(self, signal):
        """Return a list that accumulates every value emitted by *signal*."""
        received = []
        signal.connect(received.append)
        return received

    def test_sidetone_signal_on_change(self, settings):
        received = self._collect(settings.sidetone_level_changed)
        settings.sidetone_level = 64
        assert received == [64]

    def test_sidetone_signal_not_emitted_on_same_value(self, settings):
        settings.sidetone_level = 0  # already the default
        received = self._collect(settings.sidetone_level_changed)
        settings.sidetone_level = 0
        assert received == []

    def test_notify_enabled_signal(self, settings):
        received = self._collect(settings.notify_enabled_changed)
        settings.notify_enabled = True
        assert received == [True]

    def test_notify_threshold_signal(self, settings):
        received = self._collect(settings.notify_threshold_changed)
        settings.notify_threshold = 30
        assert received == [30]

    def test_lights_signal(self, settings):
        received = self._collect(settings.lights_enabled_changed)
        settings.lights_enabled = False
        assert received == [False]

    def test_chatmix_signal(self, settings):
        received = self._collect(settings.chatmix_level_changed)
        settings.chatmix_level = 32
        assert received == [32]

    def test_inactive_time_signal(self, settings):
        received = self._collect(settings.inactive_time_changed)
        settings.inactive_time = 30
        assert received == [30]

    def test_fill_color_signal(self, settings):
        received = self._collect(settings.icon_fill_color_changed)
        settings.icon_fill_color = "#FF0000"
        assert received == ["#FF0000"]

    def test_border_color_signal(self, settings):
        received = self._collect(settings.icon_border_color_changed)
        settings.icon_border_color = "#000000"
        assert received == ["#000000"]

    def test_orientation_signal(self, settings):
        received = self._collect(settings.icon_orientation_changed)
        settings.icon_orientation = "Vertical"
        assert received == ["Vertical"]

    def test_scale_signal(self, settings):
        received = self._collect(settings.icon_scale_changed)
        settings.icon_scale = 100
        assert received == [100]

    def test_show_text_signal(self, settings):
        received = self._collect(settings.icon_show_text_changed)
        settings.icon_show_text = False
        assert received == [False]

    def test_invalid_value_does_not_emit_signal(self, settings):
        """Clamped-to-same-value writes must not emit a spurious signal."""
        settings.inactive_time = 0  # already default
        received = self._collect(settings.inactive_time_changed)
        settings.inactive_time = 45  # invalid → clamped to 0 → no change
        assert received == []


# ---------------------------------------------------------------------------
# Batch operations
# ---------------------------------------------------------------------------

class TestBatchOps:
    def test_get_all_returns_all_keys(self, settings):
        result = settings.get_all()
        expected = {
            "notify_enabled", "notify_threshold", "lights_enabled",
            "sidetone_level", "chatmix_level", "inactive_time",
            "icon_fill_color", "icon_border_color", "icon_orientation",
            "icon_scale", "icon_show_text", "poll_interval",
        }
        assert result.keys() == expected

    def test_get_all_reflects_current_values(self, settings):
        settings.sidetone_level = 96
        settings.notify_enabled = True
        result = settings.get_all()
        assert result["sidetone_level"] == 96
        assert result["notify_enabled"] is True

    def test_reset_to_defaults_restores_all(self, settings):
        settings.sidetone_level = 96
        settings.notify_enabled = True
        settings.icon_scale = 120
        settings.icon_orientation = "Vertical"

        settings.reset_to_defaults()

        assert settings.sidetone_level == 0
        assert settings.notify_enabled is False
        assert settings.icon_scale == 75
        assert settings.icon_orientation == "Horizontal"

    def test_reset_emits_signals_for_changed_values(self, settings):
        settings.sidetone_level = 96  # change from default

        received = []
        settings.sidetone_level_changed.connect(received.append)
        settings.reset_to_defaults()

        assert 0 in received  # reset fired signal with default value


# ---------------------------------------------------------------------------
# Hex color validation
# ---------------------------------------------------------------------------

class TestColorValidation:
    def test_valid_lowercase_hex_accepted(self, settings):
        settings.icon_fill_color = "#aabbcc"
        assert settings.icon_fill_color == "#aabbcc"

    def test_valid_uppercase_hex_accepted(self, settings):
        settings.icon_fill_color = "#AABBCC"
        assert settings.icon_fill_color == "#AABBCC"

    def test_valid_mixed_case_hex_accepted(self, settings):
        settings.icon_fill_color = "#aAbBcC"
        assert settings.icon_fill_color == "#aAbBcC"

    def test_invalid_no_hash_rejected(self, settings):
        original = settings.icon_fill_color
        settings.icon_fill_color = "FF0000"
        assert settings.icon_fill_color == original

    def test_invalid_short_hex_rejected(self, settings):
        original = settings.icon_fill_color
        settings.icon_fill_color = "#FFF"
        assert settings.icon_fill_color == original

    def test_invalid_8digit_hex_rejected(self, settings):
        original = settings.icon_fill_color
        settings.icon_fill_color = "#FF0000FF"
        assert settings.icon_fill_color == original

    def test_invalid_non_hex_chars_rejected(self, settings):
        original = settings.icon_fill_color
        settings.icon_fill_color = "#GGHHII"
        assert settings.icon_fill_color == original

    def test_empty_string_rejected(self, settings):
        original = settings.icon_fill_color
        settings.icon_fill_color = ""
        assert settings.icon_fill_color == original

    def test_invalid_color_does_not_emit_signal(self, settings):
        received = []
        settings.icon_fill_color_changed.connect(received.append)
        settings.icon_fill_color = "not-a-color"
        assert received == []

    def test_border_color_same_validation(self, settings):
        original = settings.icon_border_color
        settings.icon_border_color = "invalid"
        assert settings.icon_border_color == original

    def test_border_color_valid_accepted(self, settings):
        settings.icon_border_color = "#123456"
        assert settings.icon_border_color == "#123456"


# ---------------------------------------------------------------------------
# Poll interval
# ---------------------------------------------------------------------------

class TestPollInterval:
    def test_default(self, settings):
        assert settings.poll_interval == 60

    def test_set_valid(self, settings):
        settings.poll_interval = 120
        assert settings.poll_interval == 120

    def test_clamps_above_max(self, settings):
        settings.poll_interval = 999
        assert settings.poll_interval == 300

    def test_clamps_below_min(self, settings):
        settings.poll_interval = 1
        assert settings.poll_interval == 10

    def test_signal_emitted_on_change(self, settings):
        received = []
        settings.poll_interval_changed.connect(received.append)
        settings.poll_interval = 90
        assert received == [90]

    def test_signal_not_emitted_on_same_value(self, settings):
        received = []
        settings.poll_interval_changed.connect(received.append)
        settings.poll_interval = 60  # already default
        assert received == []

    def test_reset_restores_default(self, settings):
        settings.poll_interval = 180
        settings.reset_to_defaults()
        assert settings.poll_interval == 60
