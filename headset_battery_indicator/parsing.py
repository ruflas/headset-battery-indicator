"""
headset_battery_indicator.parsing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pure functions to parse headsetcontrol output.

headsetcontrol emits JSON when called with ``-o json``.  These functions try
JSON first and fall back to the legacy plain-text format transparently, so the
rest of the application is insulated from headsetcontrol version differences.

Return dict schema
------------------
status      : "ok" | "unavailable" | "error"
name        : device name string
level       : int 0-100           (only when status == "ok")
level_str   : e.g. "75%"          (only when status == "ok")
is_charging : bool                (only when status == "ok")
error       : reason string       (only when status == "error")
"""

import json
import re


def _parse_json(data: dict) -> dict:
    """Parse a headsetcontrol JSON payload into a normalised status dict.

    Expected structure (headsetcontrol v3+)::

        {
          "devices": [{
            "device": "<name>",
            "battery": {
              "battery_level":  <int 0-100>,
              "battery_status": "BATTERY_AVAILABLE | BATTERY_CHARGING | BATTERY_UNAVAILABLE"
            }
          }]
        }

    The alternate key names ``"level"`` / ``"status"`` used by some older JSON
    builds are also accepted.
    """
    devices = data.get("devices", [])
    if not devices:
        return {"status": "error", "error": "No devices found", "name": "Unknown Headset"}

    dev = devices[0]
    device_name = dev.get("device") or "Unknown Headset"

    battery = dev.get("battery")
    if not battery:
        return {"status": "error", "error": "Disconnected", "name": device_name}

    # Accept both naming conventions found in the wild
    level = battery.get("battery_level", battery.get("level"))
    status_str = battery.get("battery_status", battery.get("status", ""))

    if status_str == "BATTERY_UNAVAILABLE":
        return {"status": "unavailable", "name": device_name}

    if level is None:
        return {"status": "error", "error": "Disconnected", "name": device_name}

    try:
        numeric_level = int(level)
    except (ValueError, TypeError):
        return {"status": "error", "error": "Disconnected", "name": device_name}

    is_charging = (status_str == "BATTERY_CHARGING")

    return {
        "status": "ok",
        "level": numeric_level,
        "level_str": f"{numeric_level}%",
        "is_charging": is_charging,
        "name": device_name,
    }


def _parse_text(output: str) -> dict:
    """Parse headsetcontrol plain-text output (fallback for older versions)."""
    device_name = "Unknown Headset"
    for line in output.splitlines():
        clean_line = line.strip()
        if not clean_line or clean_line.startswith(
            ("Found 1", "Status:", "Level:", "HeadsetControl")
        ):
            continue
        if "[" in clean_line and "0x" in clean_line:
            match = re.search(r"^(.*?)\[0x", clean_line)
            if match:
                name_candidate = match.group(1).strip()
                if len(name_candidate) > 1:
                    device_name = name_candidate
                    break
        elif "(" in clean_line and ")" in clean_line:
            match = re.search(r"\((.*?)\)", clean_line)
            if match:
                name_candidate = match.group(1).strip()
                if len(name_candidate) > 1:
                    device_name = name_candidate
                    break

    level_match = re.search(r"Level:\s*(\d+)%", output)
    status_match = re.search(r"Status:\s*(BATTERY_CHARGING)", output)

    if not level_match:
        if "BATTERY_UNAVAILABLE" in output:
            return {"status": "unavailable", "name": device_name}
        return {"status": "error", "error": "Disconnected", "name": device_name}

    numeric_level = int(level_match.group(1))
    is_charging = status_match is not None

    return {
        "status": "ok",
        "level": numeric_level,
        "level_str": f"{numeric_level}%",
        "is_charging": is_charging,
        "name": device_name,
    }


def parse_headsetcontrol_output(raw_output: str) -> dict:
    """Parse headsetcontrol output, preferring JSON over plain text.

    Tries to decode *raw_output* as JSON; on failure falls back to the
    regex-based text parser, so both old and new headsetcontrol builds work.
    """
    stripped = raw_output.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            data = json.loads(stripped)
            return _parse_json(data)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError, AttributeError):
            pass  # fall through to text parsing
    return _parse_text(raw_output)
