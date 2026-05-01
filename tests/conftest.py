"""
tests.conftest
~~~~~~~~~~~~~~
Shared pytest fixtures for the headset_battery_indicator test suite.
"""

import pytest
from PySide6.QtCore import QSettings


@pytest.fixture
def settings(qapp, tmp_path, monkeypatch):
    """AppSettings instance backed by a throw-away INI file.

    QSettings is redirected to a per-test temp file so real user settings
    are never read or written during testing.
    """
    ini = str(tmp_path / "settings.ini")
    monkeypatch.setattr(
        "headset_battery_indicator.settings.QSettings",
        lambda: QSettings(ini, QSettings.Format.IniFormat),
    )
    from headset_battery_indicator.settings import AppSettings
    return AppSettings()
