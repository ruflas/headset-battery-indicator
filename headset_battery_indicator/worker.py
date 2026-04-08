"""
headset_battery_indicator.worker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Background QThread that queries headsetcontrol and emits parsed battery data.
"""

import subprocess
import os
import logging

from PySide6.QtCore import QThread, Signal
from .parsing import parse_headsetcontrol_output

logger = logging.getLogger(__name__)

# Suppress the console window on Windows; no-op on Linux/macOS
CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0


class BatteryWorker(QThread):
    """
    Runs headsetcontrol in a background thread and emits the parsed result
    via status_received so the UI thread is never blocked.
    """
    status_received = Signal(dict)

    def __init__(self, binary_path: str, use_test_device: bool):
        super().__init__()
        self.binary_path = binary_path
        self.use_test_device = use_test_device

    def run(self):
        """Executed in a separate thread by Qt."""
        if not self.binary_path:
            self.status_received.emit({"status": "error", "error": "Binary Missing"})
            return

        try:
            cmd_args = [self.binary_path]
            if self.use_test_device:
                cmd_args.extend(['--test-device', '[0xf00b:0xa00c]'])
            cmd_args.extend(['-o', 'json', '-b'])

            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW
            )
            # Some headsetcontrol versions write to stderr on non-zero exit
            output = result.stdout or result.stderr
            logger.debug(f"headsetcontrol exit={result.returncode}, output={output!r}")
            self.status_received.emit(parse_headsetcontrol_output(output))

        except Exception as e:
            logger.error(f"Unexpected exception in BatteryWorker: {e}")
            self.status_received.emit({"status": "error", "error": "Execution Failed"})
