# Changelog

## 2.2.1 (2026-05-21)
- **Feat:** Internationalization (i18n) — all UI strings are now translatable; Spanish translation included.
- **Feat:** Language selector in Preferences (detects available translations automatically; restart required).
- **Feat:** "When disconnected" icon style in Preferences — choose between empty battery (default), error/X icon, or hiding the tray icon entirely (closes [#7](https://github.com/ruflas/headset-battery-indicator/issues/7)).
- **Fix:** Translation loading now uses the `QLocale` overload of `QTranslator::load()` for correct `es_ES` → `es` fallback.
- **Fix:** Tray icon visibility is restored automatically when the headset reconnects after being in "hide" mode.
- **Fix:** Orientation preference no longer breaks when the UI language changes (value stored internally in English, displayed in the active language).
- **Chore:** RPM package renamed back to `headset-battery-indicator` (was incorrectly named `python-headset-battery-indicator`); added `Obsoletes`/`Provides` for seamless upgrade.
- **CI:** Workflow now builds AppImage (Linux) and `.exe` (Windows) on tag push and uploads them automatically to the GitHub Release.

## 2.2.0 (2026-05-02)
- **Feat:** Configurable poll interval (10–300 s, default 60 s) in Preferences dialog.
- **Feat:** Notification threshold now a free-range SpinBox (5–95 %) instead of five fixed presets; moved from tray menu to Preferences dialog.
- **Feat:** Color fields in Preferences show a swatch button + editable `#RRGGBB` text input; hex values can be typed directly and are validated on entry.
- **Fix:** `subprocess.run` in worker now carries a 10 s timeout; `headsetcontrol` hangs no longer block the polling thread indefinitely.
- **Fix:** `run_headset_command` timeout also set to 10 s; `subprocess.TimeoutExpired` added to its caught exceptions.
- **Tests:** 7 new tests for `poll_interval`; updated boundary tests for `notify_threshold`.

## 2.1 (2026-04-13)
- **Fix:** `notified_low_battery` not initialized in `__init__` (potential `AttributeError` on first poll with notifications enabled).
- **Fix:** `_paint_vertical` ignored the `pen_width` parameter and recalculated without the `max(6, …)` clamp, producing thinner borders than horizontal mode at small scales.
- **Fix:** `RuntimeError: Internal C++ object already deleted` when `update_status` fired while the previous `BatteryWorker` C++ object had already been destroyed by `deleteLater`.
- **Fix:** `apply_saved_settings` blocked `__init__` with up to 4 synchronous subprocess calls; deferred to first event-loop tick via `QTimer.singleShot`.
- **Fix:** Module loggers (`worker`, `parsing`, `settings`, `icon_renderer`) were not captured by the rotating file handler.
- **Fix:** `QActionGroup` wrappers could be garbage-collected by Python; explicit list keeps references alive.
- **Fix:** `run_headset_command` caught bare `Exception`; narrowed to `subprocess.CalledProcessError, OSError`.
- **Fix:** `open_log_folder` used platform-specific `subprocess`/`os.startfile`; replaced with `QDesktopServices.openUrl`.
- **Refactor:** Extracted `HeadsetBatteryTray` → `tray.py` and `PreferencesDialog` → `preferences_dialog.py`; `__main__.py` reduced to entry point + logging setup.
- **Refactor:** Eliminated 116-line dead-code block (`paint_battery_icon` was never called).
- **Refactor:** `_make_level_menu` helper removes 3× duplicated submenu-building boilerplate.
- **Feat:** Hex color validation in `AppSettings` (`#RRGGBB` only); invalid values are rejected with a warning and do not emit signals.
- **Chore:** Added `.gitattributes` to enforce LF line endings.
- **Tests:** Added `test_settings.py` (51 tests) and `test_icon_renderer.py` (28 tests); shared fixture moved to `conftest.py`.

## 2.0.2 (2026-03-29)
- **Fix:** Resolved startup crash on Linux and macOS caused by Windows-only `os.startfile` dependency.
- **Fix:** Proper file explorer integration on all platforms.

## 2.0.1 (2026-03-26)
- **Fix:** Device name parsing for both legacy bracket format and new parentheses format (headsetcontrol 3.x).
- **Fix:** Graceful handling when headset powers off mid-session.
- **Feat:** Manual refresh button added to the tray menu.

## 2.0.0 (2025-12-11)
- **New:** Real-time dynamic icon generation; removed SVG asset dependency entirely.
- **New:** Preferences dialog for customization (fill color, border color, orientation, zoom, text overlay).
- **New:** Multi-threaded hardware polling — UI never freezes during device queries.
- **Refactor:** Complete code cleanup and architecture overhaul.

## 1.4.2 (2025-12-07)
- **New:** Windows support with native File Explorer integration for log folder.
- **New:** Cross-platform debug console.
- **New:** PyInstaller support for standalone executable packaging.

## 1.4.0 (2025-12-07)
- **New:** Bundled SVG icon assets (Adwaita-based) with smart fallback system.
- **Fix:** Crash on minimalist window managers (i3wm, etc.) where system icon themes are absent.

## 1.3.0 (2025-10-27)
- **New:** Robust dependency checking at startup.
- **New:** Integrated logging with rotating log files.
- **New:** Advanced debug menu with troubleshooting actions.

## 1.2.0 (2025-10-27)
- **New:** ChatMix control (0–128 levels).
- **New:** Auto-off time configuration.
- **New:** Persistent settings via `QSettings`.

## 1.1.0 (2025-10-26)
- **New:** Sidetone and LED light controls in the tray menu.
- **New:** Configurable low-battery notifications.
- **New:** Settings saved between sessions.
- **New:** `-debug` and `-h` command-line arguments.

## 1.0.0
- Initial release: battery monitoring and system tray icon.
