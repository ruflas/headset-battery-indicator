"""
headset_battery_indicator.worker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Background QThread that queries headsetcontrol and emits parsed battery data.
"""

import subprocess
import os
import logging

from .parsing import parse_headsetcontrol_output

logger = logging.getLogger(__name__)

# Suppress the console window on Windows; no-op on Linux/macOS
CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0


def fetch_battery_status(binary_path: str, use_test_device: bool) -> dict:
    """Run headsetcontrol and return a parsed status dict.

    Pure function with no Qt dependency — designed to be called from a
    background thread and easily unit-tested with a mocked subprocess.
    """
    if not binary_path:
        return {"status": "error", "error": "Binary Missing"}

    try:
        cmd_args = [binary_path]
        if use_test_device:
            cmd_args.extend(['--test-device', '[0xf00b:0xa00c]'])
        cmd_args.extend(['-o', 'json', '-b'])

        result = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=CREATE_NO_WINDOW
        )
        # Some headsetcontrol versions write to stderr on non-zero exit
        output = result.stdout or result.stderr
        logger.debug(f"headsetcontrol exit={result.returncode}, output={output!r}")
        return parse_headsetcontrol_output(output)

    except subprocess.TimeoutExpired:
        logger.error("headsetcontrol timed out after 10s")
        return {"status": "error", "error": "Timeout"}
    except Exception as e:
        logger.error(f"Unexpected exception in fetch_battery_status: {e}")
        return {"status": "error", "error": "Execution Failed"}


def apply_headset_settings(
    binary_path: str,
    use_test_device: bool,
    lights_enabled: bool,
    sidetone_level: int,
    chatmix_level: int,
    inactive_time: int,
) -> list:
    """Run the startup headsetcontrol commands and return the ones that failed.

    Pure function with no Qt dependency — designed to be called from a
    background thread so it never blocks the GUI event loop.
    """
    commands = [
        ["-l", "1" if lights_enabled else "0"],
        ["-s", str(sidetone_level)],
        ["-m", str(chatmix_level)],
        ["-i", str(inactive_time)],
    ]

    failed = []
    for args in commands:
        cmd = [binary_path]
        if use_test_device:
            cmd.extend(["--test-device", "[0xf00b:0xa00c]"])
        cmd.extend(args)

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=CREATE_NO_WINDOW,
            )
            logger.info(f"Ran command: {' '.join(cmd)}")
        except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired) as e:
            logger.error(f"Command failed: {' '.join(cmd)} — {e}")
            failed.append(" ".join(cmd))

    return failed


try:
    from PySide6.QtCore import QThread, Signal

    class BatteryWorker(QThread):
        """
        Thin Qt wrapper: runs fetch_battery_status() in a background thread and
        emits the result via status_received so the UI thread is never blocked.
        """
        status_received = Signal(dict)

        def __init__(self, binary_path: str, use_test_device: bool):
            super().__init__()
            self.binary_path = binary_path
            self.use_test_device = use_test_device

        def run(self):
            """Executed in a separate thread by Qt."""
            self.status_received.emit(
                fetch_battery_status(self.binary_path, self.use_test_device)
            )

    class ApplySettingsWorker(QThread):
        """
        Runs the startup headsetcontrol commands (lights, sidetone, chatmix,
        auto-off) in a background thread, so they never block the GUI event
        loop and delay delivery of the first BatteryWorker result.
        """
        finished_with_errors = Signal(list)

        def __init__(
            self,
            binary_path: str,
            use_test_device: bool,
            lights_enabled: bool,
            sidetone_level: int,
            chatmix_level: int,
            inactive_time: int,
        ):
            super().__init__()
            self.binary_path = binary_path
            self.use_test_device = use_test_device
            self.lights_enabled = lights_enabled
            self.sidetone_level = sidetone_level
            self.chatmix_level = chatmix_level
            self.inactive_time = inactive_time

        def run(self):
            """Executed in a separate thread by Qt."""
            failed = apply_headset_settings(
                self.binary_path,
                self.use_test_device,
                self.lights_enabled,
                self.sidetone_level,
                self.chatmix_level,
                self.inactive_time,
            )
            self.finished_with_errors.emit(failed)

except ImportError:
    pass  # Workers unavailable without PySide6 (e.g. in headless test environments)
