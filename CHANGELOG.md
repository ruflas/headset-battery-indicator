# Changelog

## 2.0.3 (2025-XX-XX)
- **Fix:** `notified_low_battery` not initialized in `__init__` (potential `AttributeError` on first poll with notifications enabled).
- **Fix:** `_paint_vertical` ignored the `pen_width` parameter and recalculated without the `max(6, …)` clamp, producing thinner borders than horizontal mode at small scales.
- **Fix:** `RuntimeError: Internal C++ object already deleted` when `update_status` fired while the previous `BatteryWorker` C++ object had already been destroyed by `deleteLater`.
- **Fix:** `apply_saved_settings` blocked `__init__` with up to 4 synchronous subprocess calls; deferred to first event-loop tick via `QTimer.singleShot`.
- **Fix:** Module loggers (`worker`, `parsing`, `settings`, `icon_renderer`) were not captured by the rotating file handler; handler now attached to the package-level logger.
- **Fix:** `QActionGroup` wrappers could be garbage-collected by Python; explicit list keeps references alive.
- **Fix:** `run_headset_command` caught bare `Exception`; narrowed to `subprocess.CalledProcessError, OSError`.
- **Fix:** `open_log_folder` used platform-specific `subprocess`/`os.startfile`; replaced with `QDesktopServices.openUrl`.
- **Refactor:** Extracted `HeadsetBatteryTray` → `tray.py` and `PreferencesDialog` → `preferences_dialog.py`; `__main__.py` reduced to entry point + logging setup.
- **Refactor:** Eliminated 116-line dead-code block (`paint_battery_icon` was never called).
- **Refactor:** `_make_level_menu` helper removes 3× duplicated submenu-building boilerplate.
- **Feat:** Hex color validation in `AppSettings` (`#RRGGBB` only); invalid values are rejected with a warning and do not emit signals.
- **Chore:** Added `.gitattributes` to enforce LF line endings.
- **Tests:** Added `test_settings.py` (51 tests) and `test_icon_renderer.py` (28 tests); shared fixture moved to `conftest.py`; CI updated with `xvfb-run` and `pytest-qt`.

## 2.0.0 (2025-XX-XX)
- **New:** Real-time dynamic icon generation (removed SVG dependency).
- **New:** Preferences dialog for customization (Colors, Orientation, Zoom).
- **New:** Multi-threaded hardware polling (UI no longer freezes).
- **Refactor:** Complete code cleanup and optimization.

## 1.1.0 (2025-10-26)
- Added Sidetone and Light controls to the tray menu.
- Added configurable low-battery notifications.
- Settings are now saved between sessions.
- Added `-debug` and `-h` command-line arguments.

## 1.0.0
- Initial release.
- Battery monitoring and tray icon.
