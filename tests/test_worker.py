"""
Tests for headset_battery_indicator.worker.fetch_battery_status

fetch_battery_status is a pure function (no Qt) so it can be tested by simply
mocking subprocess.run — no QApplication or event loop needed.
"""

import subprocess
from unittest.mock import patch, MagicMock

import pytest

from headset_battery_indicator.worker import fetch_battery_status


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(stdout="", stderr="", returncode=0):
    """Build a fake subprocess.CompletedProcess."""
    r = MagicMock(spec=subprocess.CompletedProcess)
    r.stdout = stdout
    r.stderr = stderr
    r.returncode = returncode
    return r


JSON_AVAILABLE = '{"devices":[{"device":"Arctis 7","battery":{"battery_level":80,"battery_status":"BATTERY_AVAILABLE"}}]}'
JSON_CHARGING  = '{"devices":[{"device":"Arctis 7","battery":{"battery_level":40,"battery_status":"BATTERY_CHARGING"}}]}'
JSON_UNAVAIL   = '{"devices":[{"device":"Arctis 7","battery":{"battery_level":0,"battery_status":"BATTERY_UNAVAILABLE"}}]}'

TEXT_AVAILABLE = (
    "HeadsetControl: 2.7.0\nFound 1 Device(s)\n"
    "Arctis 7 [0xabcd:0x1234]\nStatus: BATTERY_AVAILABLE\nLevel: 55%\n"
)


# ---------------------------------------------------------------------------
# No binary
# ---------------------------------------------------------------------------

class TestNoBinary:
    def test_empty_string_path(self):
        result = fetch_battery_status("", False)
        assert result == {"status": "error", "error": "Binary Missing"}

    def test_none_path(self):
        result = fetch_battery_status(None, False)
        assert result == {"status": "error", "error": "Binary Missing"}


# ---------------------------------------------------------------------------
# Normal subprocess operation
# ---------------------------------------------------------------------------

class TestFetchBatteryStatus:
    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_json_available(self, mock_run):
        mock_run.return_value = _make_result(stdout=JSON_AVAILABLE)
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        assert result["status"] == "ok"
        assert result["level"] == 80
        assert result["is_charging"] is False
        assert result["name"] == "Arctis 7"

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_json_charging(self, mock_run):
        mock_run.return_value = _make_result(stdout=JSON_CHARGING)
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        assert result["status"] == "ok"
        assert result["is_charging"] is True
        assert result["level"] == 40

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_json_unavailable(self, mock_run):
        mock_run.return_value = _make_result(stdout=JSON_UNAVAIL)
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        assert result["status"] == "unavailable"

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_text_fallback(self, mock_run):
        """Older headsetcontrol without JSON support → plain text, still parsed."""
        mock_run.return_value = _make_result(stdout=TEXT_AVAILABLE)
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        assert result["status"] == "ok"
        assert result["level"] == 55
        assert result["name"] == "Arctis 7"

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_stderr_used_when_stdout_empty(self, mock_run):
        """headsetcontrol writes to stderr on non-zero exit."""
        mock_run.return_value = _make_result(stdout="", stderr=JSON_AVAILABLE, returncode=1)
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        assert result["status"] == "ok"
        assert result["level"] == 80

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_both_stdout_and_stderr_prefers_stdout(self, mock_run):
        mock_run.return_value = _make_result(stdout=JSON_AVAILABLE, stderr="some error", returncode=0)
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        assert result["status"] == "ok"

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_empty_output_returns_error(self, mock_run):
        mock_run.return_value = _make_result(stdout="", stderr="")
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        assert result["status"] == "error"

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_non_zero_exit_still_parsed(self, mock_run):
        """Non-zero exit code alone should not cause an error if output is valid."""
        mock_run.return_value = _make_result(stdout=JSON_AVAILABLE, returncode=2)
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        assert result["status"] == "ok"


# ---------------------------------------------------------------------------
# Test device flag
# ---------------------------------------------------------------------------

class TestTestDeviceFlag:
    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_test_device_args_passed(self, mock_run):
        mock_run.return_value = _make_result(stdout=JSON_AVAILABLE)
        fetch_battery_status("/usr/bin/headsetcontrol", use_test_device=True)
        call_args = mock_run.call_args[0][0]
        assert "--test-device" in call_args
        assert "[0xf00b:0xa00c]" in call_args

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_no_test_device_args_when_false(self, mock_run):
        mock_run.return_value = _make_result(stdout=JSON_AVAILABLE)
        fetch_battery_status("/usr/bin/headsetcontrol", use_test_device=False)
        call_args = mock_run.call_args[0][0]
        assert "--test-device" not in call_args

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_json_flag_always_present(self, mock_run):
        mock_run.return_value = _make_result(stdout=JSON_AVAILABLE)
        fetch_battery_status("/usr/bin/headsetcontrol", False)
        call_args = mock_run.call_args[0][0]
        assert "-o" in call_args
        assert "json" in call_args
        assert "-b" in call_args


# ---------------------------------------------------------------------------
# Exception handling
# ---------------------------------------------------------------------------

class TestExceptions:
    @patch("headset_battery_indicator.worker.subprocess.run", side_effect=FileNotFoundError("not found"))
    def test_file_not_found(self, mock_run):
        result = fetch_battery_status("/nonexistent/headsetcontrol", False)
        assert result == {"status": "error", "error": "Execution Failed"}

    @patch("headset_battery_indicator.worker.subprocess.run", side_effect=PermissionError("denied"))
    def test_permission_error(self, mock_run):
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        assert result == {"status": "error", "error": "Execution Failed"}

    @patch("headset_battery_indicator.worker.subprocess.run", side_effect=OSError("broken"))
    def test_generic_os_error(self, mock_run):
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        assert result == {"status": "error", "error": "Execution Failed"}


# ---------------------------------------------------------------------------
# Command construction
# ---------------------------------------------------------------------------

class TestCommandConstruction:
    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_binary_path_is_first_arg(self, mock_run):
        mock_run.return_value = _make_result(stdout=JSON_AVAILABLE)
        fetch_battery_status("/usr/local/bin/headsetcontrol", False)
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "/usr/local/bin/headsetcontrol"

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_binary_path_with_spaces(self, mock_run):
        # Paths with spaces must be passed as a list element, not shell-split
        mock_run.return_value = _make_result(stdout=JSON_AVAILABLE)
        fetch_battery_status("/home/user/my tools/headsetcontrol", False)
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "/home/user/my tools/headsetcontrol"

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_test_device_args_come_before_flags(self, mock_run):
        mock_run.return_value = _make_result(stdout=JSON_AVAILABLE)
        fetch_battery_status("/usr/bin/headsetcontrol", use_test_device=True)
        call_args = mock_run.call_args[0][0]
        td_index = call_args.index("--test-device")
        json_index = call_args.index("-o")
        assert td_index < json_index

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_capture_output_and_text_mode(self, mock_run):
        mock_run.return_value = _make_result(stdout=JSON_AVAILABLE)
        fetch_battery_status("/usr/bin/headsetcontrol", False)
        kwargs = mock_run.call_args[1]
        assert kwargs.get("capture_output") is True
        assert kwargs.get("text") is True


# ---------------------------------------------------------------------------
# Output content edge cases
# ---------------------------------------------------------------------------

class TestOutputEdgeCases:
    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_crlf_output_parsed_correctly(self, mock_run):
        # Windows-style line endings in headsetcontrol output
        text = "My Headset [0xabcd:0x1234]\r\nStatus: BATTERY_AVAILABLE\r\nLevel: 72%\r\n"
        mock_run.return_value = _make_result(stdout=text)
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        assert result["status"] == "ok"
        assert result["level"] == 72

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_unicode_device_name(self, mock_run):
        raw = '{"devices":[{"device":"SteelSeries Arctis Növa","battery":{"battery_level":55,"battery_status":"BATTERY_AVAILABLE"}}]}'
        mock_run.return_value = _make_result(stdout=raw)
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        assert result["name"] == "SteelSeries Arctis Növa"

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_result_always_has_status_key(self, mock_run):
        # Invariant holds even with garbage output
        mock_run.return_value = _make_result(stdout="total garbage output %%%")
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        assert "status" in result

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_stderr_fallback_on_returncode_nonzero(self, mock_run):
        # Device disconnected: headsetcontrol exits 1 and writes JSON to stderr
        mock_run.return_value = _make_result(
            stdout="",
            stderr='{"devices":[{"device":"Arctis 7","battery":{"battery_level":0,"battery_status":"BATTERY_UNAVAILABLE"}}]}',
            returncode=1,
        )
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        assert result["status"] == "unavailable"

    @patch("headset_battery_indicator.worker.subprocess.run")
    def test_malformed_json_in_stdout_falls_back_to_text_in_stderr(self, mock_run):
        # stdout has broken JSON, stderr has valid text — stdout wins and falls back to text
        mock_run.return_value = _make_result(
            stdout="{broken",
            stderr="My Headset [0x1234:0x5678]\nLevel: 40%\n",
        )
        result = fetch_battery_status("/usr/bin/headsetcontrol", False)
        # stdout is non-empty so it's used; broken JSON falls back to text parsing of stdout
        assert result["status"] == "error"  # "{broken" has no Level: line as text
