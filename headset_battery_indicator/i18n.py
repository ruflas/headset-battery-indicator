"""
headset_battery_indicator.i18n
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Translation helpers: scan available languages and install a QTranslator.
"""

import glob
import os
import re

from PySide6.QtCore import QLocale, QTranslator
from PySide6.QtWidgets import QApplication

TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), "translations")


def available_languages() -> list:
    """Return [(code, native_name), ...] for all bundled translations.

    Always includes ("system", ...) and ("en", "English") first.
    """
    entries = [("system", "System Default"), ("en", "English")]
    pattern = os.path.join(TRANSLATIONS_DIR, "headset_battery_indicator_*.qm")
    for path in sorted(glob.glob(pattern)):
        m = re.match(r"headset_battery_indicator_(.+)\.qm", os.path.basename(path))
        if m:
            code = m.group(1)
            if code == "en":
                continue
            name = QLocale(code).nativeLanguageName() or code
            if name:
                name = name[0].upper() + name[1:]
            entries.append((code, name))
    return entries


def install_translator(app: QApplication, language: str) -> None:
    """Load and install a QTranslator for *language*.

    "system" uses the OS locale, "en" skips translation entirely,
    any other value is treated as a locale/language code.
    """
    if language == "en":
        return
    locale = QLocale.system() if language == "system" else QLocale(language)
    translator = QTranslator(app)
    if translator.load(locale, "headset_battery_indicator", "_", TRANSLATIONS_DIR):
        app.installTranslator(translator)
