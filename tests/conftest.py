"""
tests.conftest
~~~~~~~~~~~~~~
Shared pytest fixtures for the headset_battery_indicator test suite.
"""

import pytest


@pytest.fixture
def settings(qapp, tmp_path, monkeypatch):
    """AppSettings instance backed by a throw-away INI file.

    The settings file path is redirected to a per-test temp file so real
    user settings are never read or written during testing.
    """
    ini = str(tmp_path / "settings.ini")
    monkeypatch.setattr("headset_battery_indicator.settings.SETTINGS_FILE", ini)
    from headset_battery_indicator.settings import AppSettings
    return AppSettings()
