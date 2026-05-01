"""
tests.test_icon_renderer
~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for BatteryIconRenderer.

Constructor tests run without a QApplication (pure Python attribute checks).
Render tests require a QApplication and are handled automatically by pytest-qt
via the `qapp` fixture.
"""

import pytest
from PySide6.QtGui import QIcon

from headset_battery_indicator.icon_renderer import BatteryIconRenderer


# ---------------------------------------------------------------------------
# Constructor — no QApplication required
# ---------------------------------------------------------------------------

class TestInit:
    def test_default_fill_color(self):
        assert BatteryIconRenderer().fill_color == "#00FF00"

    def test_default_border_color(self):
        assert BatteryIconRenderer().border_color == "#FFFFFF"

    def test_default_orientation(self):
        assert BatteryIconRenderer().orientation == "Horizontal"

    def test_default_scale(self):
        assert BatteryIconRenderer().scale == 75

    def test_default_show_text(self):
        assert BatteryIconRenderer().show_text is True

    def test_custom_fill_color(self):
        r = BatteryIconRenderer(fill_color="#FF0000")
        assert r.fill_color == "#FF0000"

    def test_custom_border_color(self):
        r = BatteryIconRenderer(border_color="#0000FF")
        assert r.border_color == "#0000FF"

    def test_vertical_orientation(self):
        r = BatteryIconRenderer(orientation="Vertical")
        assert r.orientation == "Vertical"

    def test_show_text_false(self):
        r = BatteryIconRenderer(show_text=False)
        assert r.show_text is False

    # Scale clamping
    def test_scale_clamped_above_150(self):
        assert BatteryIconRenderer(scale=999).scale == 150

    def test_scale_clamped_below_50(self):
        assert BatteryIconRenderer(scale=1).scale == 50

    def test_scale_exact_lower_bound(self):
        assert BatteryIconRenderer(scale=50).scale == 50

    def test_scale_exact_upper_bound(self):
        assert BatteryIconRenderer(scale=150).scale == 150

    def test_scale_midpoint(self):
        assert BatteryIconRenderer(scale=100).scale == 100


# ---------------------------------------------------------------------------
# Rendering — QApplication required (pytest-qt provides `qapp` fixture)
# ---------------------------------------------------------------------------

class TestRender:
    def test_returns_qicon(self, qapp):
        icon = BatteryIconRenderer().render(75, False)
        assert isinstance(icon, QIcon)

    def test_not_null(self, qapp):
        icon = BatteryIconRenderer().render(75, False)
        assert not icon.isNull()

    def test_error_state_returns_qicon(self, qapp):
        icon = BatteryIconRenderer().render(0, False, error=True)
        assert isinstance(icon, QIcon)

    def test_error_icon_not_null(self, qapp):
        assert not BatteryIconRenderer().render(0, False, error=True).isNull()

    def test_charging_returns_qicon(self, qapp):
        icon = BatteryIconRenderer().render(50, True)
        assert isinstance(icon, QIcon)

    def test_zero_percent(self, qapp):
        assert not BatteryIconRenderer().render(0, False).isNull()

    def test_hundred_percent(self, qapp):
        assert not BatteryIconRenderer().render(100, False).isNull()

    def test_vertical_orientation(self, qapp):
        r = BatteryIconRenderer(orientation="Vertical")
        assert not r.render(50, False).isNull()

    def test_no_text_overlay(self, qapp):
        r = BatteryIconRenderer(show_text=False)
        assert not r.render(50, False).isNull()

    def test_small_scale(self, qapp):
        r = BatteryIconRenderer(scale=50)
        assert not r.render(50, False).isNull()

    def test_large_scale(self, qapp):
        r = BatteryIconRenderer(scale=150)
        assert not r.render(50, False).isNull()

    def test_charging_at_zero_percent(self, qapp):
        assert not BatteryIconRenderer().render(0, True).isNull()

    def test_charging_at_hundred_percent(self, qapp):
        assert not BatteryIconRenderer().render(100, True).isNull()

    # Canvas size sanity check via pixmap
    def test_icon_has_expected_canvas_size(self, qapp):
        r = BatteryIconRenderer()
        icon = r.render(50, False)
        sizes = icon.availableSizes()
        assert len(sizes) > 0
        size = sizes[0]
        assert size.width() == BatteryIconRenderer.CANVAS_SIZE
        assert size.height() == BatteryIconRenderer.CANVAS_SIZE
