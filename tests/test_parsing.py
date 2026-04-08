"""
Tests for headset_battery_indicator.parsing

Run with:  pytest tests/
"""

import pytest
from headset_battery_indicator.parsing import (
    _parse_json,
    _parse_text,
    parse_headsetcontrol_output,
)


# ---------------------------------------------------------------------------
# _parse_json
# ---------------------------------------------------------------------------

class TestParseJson:
    def _device(self, name="Corsair HS70 Pro Wireless", battery=None):
        dev = {"device": name}
        if battery is not None:
            dev["battery"] = battery
        return {"devices": [dev]}

    def test_available(self):
        data = self._device(battery={"battery_level": 75, "battery_status": "BATTERY_AVAILABLE"})
        result = _parse_json(data)
        assert result == {
            "status": "ok",
            "level": 75,
            "level_str": "75%",
            "is_charging": False,
            "name": "Corsair HS70 Pro Wireless",
        }

    def test_charging(self):
        data = self._device(battery={"battery_level": 40, "battery_status": "BATTERY_CHARGING"})
        result = _parse_json(data)
        assert result["status"] == "ok"
        assert result["is_charging"] is True
        assert result["level"] == 40

    def test_unavailable(self):
        data = self._device(battery={"battery_level": 0, "battery_status": "BATTERY_UNAVAILABLE"})
        result = _parse_json(data)
        assert result == {"status": "unavailable", "name": "Corsair HS70 Pro Wireless"}

    def test_no_battery_key(self):
        data = {"devices": [{"device": "Some Headset"}]}
        result = _parse_json(data)
        assert result["status"] == "error"
        assert result["error"] == "Disconnected"
        assert result["name"] == "Some Headset"

    def test_no_devices(self):
        result = _parse_json({"devices": []})
        assert result["status"] == "error"
        assert result["name"] == "Unknown Headset"

    def test_missing_devices_key(self):
        result = _parse_json({})
        assert result["status"] == "error"

    def test_level_none_with_available_status(self):
        # battery_status present but no level field at all
        data = self._device(battery={"battery_status": "BATTERY_AVAILABLE"})
        result = _parse_json(data)
        assert result["status"] == "error"
        assert result["error"] == "Disconnected"

    def test_alternate_key_names(self):
        # Older JSON builds use "level" / "status" instead of battery_level / battery_status
        data = self._device(battery={"level": 60, "status": "BATTERY_AVAILABLE"})
        result = _parse_json(data)
        assert result["status"] == "ok"
        assert result["level"] == 60

    def test_alternate_keys_charging(self):
        data = self._device(battery={"level": 20, "status": "BATTERY_CHARGING"})
        result = _parse_json(data)
        assert result["is_charging"] is True

    def test_alternate_keys_unavailable(self):
        data = self._device(battery={"level": 0, "status": "BATTERY_UNAVAILABLE"})
        result = _parse_json(data)
        assert result["status"] == "unavailable"

    def test_level_zero(self):
        data = self._device(battery={"battery_level": 0, "battery_status": "BATTERY_AVAILABLE"})
        result = _parse_json(data)
        assert result["status"] == "ok"
        assert result["level"] == 0
        assert result["level_str"] == "0%"

    def test_level_100(self):
        data = self._device(battery={"battery_level": 100, "battery_status": "BATTERY_AVAILABLE"})
        result = _parse_json(data)
        assert result["level"] == 100
        assert result["level_str"] == "100%"

    def test_missing_device_name_falls_back(self):
        data = {"devices": [{"battery": {"battery_level": 50, "battery_status": "BATTERY_AVAILABLE"}}]}
        result = _parse_json(data)
        assert result["name"] == "Unknown Headset"

    def test_empty_device_name_falls_back(self):
        data = self._device(name="", battery={"battery_level": 50, "battery_status": "BATTERY_AVAILABLE"})
        result = _parse_json(data)
        assert result["name"] == "Unknown Headset"

    def test_multiple_devices_uses_first(self):
        data = {
            "devices": [
                {"device": "First", "battery": {"battery_level": 80, "battery_status": "BATTERY_AVAILABLE"}},
                {"device": "Second", "battery": {"battery_level": 10, "battery_status": "BATTERY_AVAILABLE"}},
            ]
        }
        result = _parse_json(data)
        assert result["name"] == "First"
        assert result["level"] == 80

    def test_null_battery_status_treated_as_available(self):
        # headsetcontrol may emit null for status in some edge cases
        data = self._device(battery={"battery_level": 50, "battery_status": None})
        result = _parse_json(data)
        assert result["status"] == "ok"
        assert result["is_charging"] is False
        assert result["level"] == 50

    def test_unknown_battery_status_treated_as_available(self):
        # e.g. BATTERY_HIDERROR — not charging, not unavailable → show level
        data = self._device(battery={"battery_level": 60, "battery_status": "BATTERY_HIDERROR"})
        result = _parse_json(data)
        assert result["status"] == "ok"
        assert result["is_charging"] is False

    def test_battery_level_as_string_float_returns_error(self):
        # Malformed output: level is "75.5" instead of 75
        data = self._device(battery={"battery_level": "75.5", "battery_status": "BATTERY_AVAILABLE"})
        result = _parse_json(data)
        assert result["status"] == "error"

    def test_battery_level_as_non_numeric_string_returns_error(self):
        data = self._device(battery={"battery_level": "N/A", "battery_status": "BATTERY_AVAILABLE"})
        result = _parse_json(data)
        assert result["status"] == "error"

    def test_battery_level_as_string_integer_is_accepted(self):
        # Some builds stringify the level: "75" should still parse
        data = self._device(battery={"battery_level": "75", "battery_status": "BATTERY_AVAILABLE"})
        result = _parse_json(data)
        assert result["status"] == "ok"
        assert result["level"] == 75

    def test_extra_unknown_fields_ignored(self):
        # Forward-compat: future headsetcontrol may add new fields
        data = self._device(battery={
            "battery_level": 55, "battery_status": "BATTERY_AVAILABLE",
            "future_field": "something", "another": 42
        })
        result = _parse_json(data)
        assert result["status"] == "ok"
        assert result["level"] == 55

    def test_extra_top_level_fields_ignored(self):
        data = {
            "devices": [{"device": "Headset X", "battery": {"battery_level": 70, "battery_status": "BATTERY_AVAILABLE"}}],
            "version": {"major": 3, "minor": 7},
            "api_version": 2,
        }
        result = _parse_json(data)
        assert result["status"] == "ok"
        assert result["level"] == 70

    def test_charging_at_100_percent(self):
        data = self._device(battery={"battery_level": 100, "battery_status": "BATTERY_CHARGING"})
        result = _parse_json(data)
        assert result["status"] == "ok"
        assert result["level"] == 100
        assert result["is_charging"] is True

    def test_device_name_with_unicode(self):
        data = self._device(
            name="SteelSeries Arctis Növa Pro Wöreless",
            battery={"battery_level": 50, "battery_status": "BATTERY_AVAILABLE"}
        )
        result = _parse_json(data)
        assert result["name"] == "SteelSeries Arctis Növa Pro Wöreless"

    def test_level_str_format(self):
        # level_str must always be "<int>%"
        for lvl in (0, 1, 25, 99, 100):
            data = self._device(battery={"battery_level": lvl, "battery_status": "BATTERY_AVAILABLE"})
            result = _parse_json(data)
            assert result["level_str"] == f"{lvl}%"


# ---------------------------------------------------------------------------
# _parse_text
# ---------------------------------------------------------------------------

class TestParseText:
    # Typical headsetcontrol v2 output
    NORMAL = (
        "HeadsetControl: 2.7.0\n"
        "Found 1 Device(s)\n"
        "Corsair HS70 Pro Wireless [0x1b1c:0x0a55]\n"
        "Status: BATTERY_AVAILABLE\n"
        "Level: 75%\n"
    )

    CHARGING = (
        "HeadsetControl: 2.7.0\n"
        "Found 1 Device(s)\n"
        "Corsair HS70 Pro Wireless [0x1b1c:0x0a55]\n"
        "Status: BATTERY_CHARGING\n"
        "Level: 40%\n"
    )

    UNAVAILABLE = (
        "HeadsetControl: 2.7.0\n"
        "Found 1 Device(s)\n"
        "Corsair HS70 Pro Wireless [0x1b1c:0x0a55]\n"
        "Status: BATTERY_UNAVAILABLE\n"
    )

    PAREN_NAME = (
        "HeadsetControl: 2.7.0\n"
        "Found 1 Device(s)\n"
        "USB Audio Device (Arctis 7) some extra\n"
        "Status: BATTERY_AVAILABLE\n"
        "Level: 60%\n"
    )

    def test_normal(self):
        result = _parse_text(self.NORMAL)
        assert result == {
            "status": "ok",
            "level": 75,
            "level_str": "75%",
            "is_charging": False,
            "name": "Corsair HS70 Pro Wireless",
        }

    def test_charging(self):
        result = _parse_text(self.CHARGING)
        assert result["status"] == "ok"
        assert result["is_charging"] is True
        assert result["level"] == 40

    def test_unavailable(self):
        result = _parse_text(self.UNAVAILABLE)
        assert result == {"status": "unavailable", "name": "Corsair HS70 Pro Wireless"}

    def test_empty_output(self):
        result = _parse_text("")
        assert result["status"] == "error"
        assert result["error"] == "Disconnected"

    def test_no_level_line(self):
        result = _parse_text("HeadsetControl: 2.7.0\nFound 1 Device(s)\n")
        assert result["status"] == "error"

    def test_name_from_parentheses(self):
        result = _parse_text(self.PAREN_NAME)
        assert result["name"] == "Arctis 7"
        assert result["status"] == "ok"

    def test_unknown_name_when_no_match(self):
        output = "Status: BATTERY_AVAILABLE\nLevel: 50%\n"
        result = _parse_text(output)
        assert result["name"] == "Unknown Headset"
        assert result["level"] == 50

    def test_level_zero(self):
        output = "My Headset [0x1234:0x5678]\nStatus: BATTERY_AVAILABLE\nLevel: 0%\n"
        result = _parse_text(output)
        assert result["status"] == "ok"
        assert result["level"] == 0

    def test_level_100(self):
        output = "My Headset [0x1234:0x5678]\nStatus: BATTERY_AVAILABLE\nLevel: 100%\n"
        result = _parse_text(output)
        assert result["status"] == "ok"
        assert result["level"] == 100
        assert result["level_str"] == "100%"

    def test_windows_crlf_line_endings(self):
        # splitlines() handles \r\n natively
        output = "My Headset [0x1234:0x5678]\r\nStatus: BATTERY_AVAILABLE\r\nLevel: 65%\r\n"
        result = _parse_text(output)
        assert result["status"] == "ok"
        assert result["level"] == 65

    def test_multiple_level_lines_uses_first(self):
        # re.search finds the first match
        output = "My Headset [0x1234:0x5678]\nLevel: 80%\nLevel: 20%\n"
        result = _parse_text(output)
        assert result["level"] == 80

    def test_device_name_with_unicode(self):
        output = "SteelSeries Arctis Növa [0xabcd:0x1234]\nStatus: BATTERY_AVAILABLE\nLevel: 42%\n"
        result = _parse_text(output)
        assert result["name"] == "SteelSeries Arctis Növa"
        assert result["level"] == 42

    def test_status_line_before_level_line(self):
        # Status and Level can appear in any order
        output = "My Headset [0x1234:0x5678]\nLevel: 55%\nStatus: BATTERY_CHARGING\n"
        result = _parse_text(output)
        assert result["status"] == "ok"
        assert result["is_charging"] is True
        assert result["level"] == 55

    def test_battery_unavailable_takes_priority_over_missing_level(self):
        output = "My Headset [0x1234:0x5678]\nStatus: BATTERY_UNAVAILABLE\n"
        result = _parse_text(output)
        assert result["status"] == "unavailable"
        assert result["name"] == "My Headset"

    def test_output_with_no_newlines(self):
        # Degenerate single-line output
        result = _parse_text("Level: 50%")
        assert result["status"] == "ok"
        assert result["level"] == 50


# ---------------------------------------------------------------------------
# parse_headsetcontrol_output  (integration: JSON vs text dispatch)
# ---------------------------------------------------------------------------

class TestParseHeadsetcontrolOutput:
    def test_dispatches_to_json_on_valid_json(self):
        raw = '{"devices": [{"device": "Arctis 7", "battery": {"battery_level": 80, "battery_status": "BATTERY_AVAILABLE"}}]}'
        result = parse_headsetcontrol_output(raw)
        assert result["status"] == "ok"
        assert result["level"] == 80
        assert result["name"] == "Arctis 7"

    def test_dispatches_to_text_when_no_json(self):
        raw = (
            "HeadsetControl: 2.7.0\n"
            "Found 1 Device(s)\n"
            "Arctis 7 [0xabcd:0x1234]\n"
            "Status: BATTERY_AVAILABLE\n"
            "Level: 55%\n"
        )
        result = parse_headsetcontrol_output(raw)
        assert result["status"] == "ok"
        assert result["level"] == 55
        assert result["name"] == "Arctis 7"

    def test_falls_back_to_text_on_malformed_json(self):
        # Starts with '{' but is not valid JSON
        raw = (
            "{not valid json}\n"
            "Arctis 7 [0xabcd:0x1234]\n"
            "Status: BATTERY_AVAILABLE\n"
            "Level: 30%\n"
        )
        result = parse_headsetcontrol_output(raw)
        assert result["status"] == "ok"
        assert result["level"] == 30

    def test_json_charging(self):
        raw = '{"devices": [{"device": "HD 660S", "battery": {"battery_level": 20, "battery_status": "BATTERY_CHARGING"}}]}'
        result = parse_headsetcontrol_output(raw)
        assert result["is_charging"] is True

    def test_json_unavailable(self):
        raw = '{"devices": [{"device": "HD 660S", "battery": {"battery_level": 0, "battery_status": "BATTERY_UNAVAILABLE"}}]}'
        result = parse_headsetcontrol_output(raw)
        assert result["status"] == "unavailable"

    def test_empty_string(self):
        result = parse_headsetcontrol_output("")
        assert result["status"] == "error"

    def test_whitespace_only(self):
        result = parse_headsetcontrol_output("   \n  ")
        assert result["status"] == "error"

    def test_json_with_leading_whitespace(self):
        raw = '  \n{"devices": [{"device": "Test", "battery": {"battery_level": 90, "battery_status": "BATTERY_AVAILABLE"}}]}'
        result = parse_headsetcontrol_output(raw)
        assert result["status"] == "ok"
        assert result["level"] == 90

    def test_json_root_array_falls_back_to_text(self):
        # If headsetcontrol wraps output in [] instead of {}, fall back gracefully
        raw = "[]"
        result = parse_headsetcontrol_output(raw)
        assert result["status"] == "error"

    def test_json_with_null_battery_status(self):
        raw = '{"devices":[{"device":"X","battery":{"battery_level":50,"battery_status":null}}]}'
        result = parse_headsetcontrol_output(raw)
        assert result["status"] == "ok"
        assert result["is_charging"] is False

    def test_json_with_unknown_battery_status(self):
        raw = '{"devices":[{"device":"X","battery":{"battery_level":60,"battery_status":"BATTERY_HIDERROR"}}]}'
        result = parse_headsetcontrol_output(raw)
        assert result["status"] == "ok"
        assert result["is_charging"] is False

    def test_json_float_level_returns_error(self):
        raw = '{"devices":[{"device":"X","battery":{"battery_level":"75.5","battery_status":"BATTERY_AVAILABLE"}}]}'
        result = parse_headsetcontrol_output(raw)
        assert result["status"] == "error"

    def test_text_with_crlf_line_endings(self):
        raw = "My Headset [0x1234:0x5678]\r\nStatus: BATTERY_AVAILABLE\r\nLevel: 70%\r\n"
        result = parse_headsetcontrol_output(raw)
        assert result["status"] == "ok"
        assert result["level"] == 70

    def test_result_always_has_status_key(self):
        # Invariant: every possible input must produce a dict with "status"
        inputs = ["", "{}", "[]", "garbage", '{"devices":[]}', "Level: 50%"]
        for raw in inputs:
            result = parse_headsetcontrol_output(raw)
            assert "status" in result, f"Missing 'status' for input {raw!r}"

    def test_ok_result_always_has_required_keys(self):
        raw = '{"devices":[{"device":"X","battery":{"battery_level":50,"battery_status":"BATTERY_AVAILABLE"}}]}'
        result = parse_headsetcontrol_output(raw)
        for key in ("status", "level", "level_str", "is_charging", "name"):
            assert key in result
