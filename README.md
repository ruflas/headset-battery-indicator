# 🎧 Headset Battery Indicator

[![License](https://img.shields.io/github/license/ruflas/headset-battery-indicator)](LICENSE)
[![Release](https://img.shields.io/github/v/release/ruflas/headset-battery-indicator)](https://github.com/ruflas/headset-battery-indicator/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Downloads](https://img.shields.io/github/downloads/ruflas/headset-battery-indicator/total)](https://github.com/ruflas/headset-battery-indicator/releases/latest)

A lightweight, modern tray indicator that shows your **wireless headset's battery level** and **charging status**, with controls for LEDs, sidetone, ChatMix, and more — powered by [HeadsetControl](https://github.com/Sapd/HeadsetControl) and built with **PySide6 (Qt)**.

Works on **KDE Plasma**, **GNOME**, **XFCE**, **Cinnamon**, and other Linux desktop environments.

![Screenshot of the tray icon](screenshot.png)

---

## 📘 Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Option 1: AppImage (Recommended)](#option-1-appimage-recommended)
  - [Option 2: Fedora COPR](#option-2-fedora-copr)
  - [Option 3: Arch Linux (AUR)](#option-3-arch-linux-aur)
  - [Option 4: From Source](#option-4-from-source)
- [Usage](#usage)
- [Command-Line Options](#command-line-options)
- [Autostart](#autostart)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

- **Dynamic Tray Icon** — Live battery percentage and charging state rendered in real time.
- **Low-Battery Notifications** — Desktop alerts with optional headset sound when battery drops below your threshold.
- **Preferences Dialog** — Customize icon colors, orientation, scale, text overlay, poll interval, notification threshold, disconnected icon style, and language.
- **Device Control** — Toggle LEDs, adjust sidetone, set ChatMix level, and configure auto power-off time.
- **Persistent Configuration** — All preferences are saved between sessions automatically.
- **Non-Blocking Polling** — Hardware queries run in a background thread; the UI never freezes.
- **Internationalization** — UI is fully translatable; Spanish included. Language selectable in Preferences.
- **Version Menu Item** — Current version shown in the tray menu; click to open the GitHub releases page and check for updates.
- **Debug Mode** — Interactive console with live log output for troubleshooting.

---

## 🧩 Requirements

| Dependency | Description |
|---|---|
| [HeadsetControl](https://github.com/Sapd/HeadsetControl) | Hardware communication backend — must be installed separately |
| Python 3.8+ | Runtime environment |
| PySide6 | Qt GUI framework |

> ⚠️ This app **depends entirely on HeadsetControl** for hardware communication.  
> Make sure `headsetcontrol` is installed and working before running the indicator.

---

## 🚀 Installation

### Option 1: AppImage / Windows EXE (Recommended)

No need to install Python or PySide6 — just headsetcontrol.

Download the latest **AppImage** (Linux) or **EXE** (Windows) from the [Releases page](https://github.com/ruflas/headset-battery-indicator/releases/latest).

1. **Download** the latest AppImage from the [Releases page](https://github.com/ruflas/headset-battery-indicator/releases/latest).

2. **Make it executable:**
   ```bash
   chmod +x Headset_Battery_Indicator-*.AppImage
   ```

3. **Run it:**
   ```bash
   ./Headset_Battery_Indicator-*.AppImage
   ```

You can move it to `~/.local/bin` and add it to your desktop's autostart list.

---

### Option 2: Fedora COPR

```bash
sudo dnf copr enable ruflas/headset-battery-indicator
sudo dnf install headset-battery-indicator
```

---

### Option 3: Arch Linux (AUR)

Install using your AUR helper of choice:

```bash
yay -S headset-battery-indicator-git
# or
paru -S headset-battery-indicator-git
```

> Community-maintained [AUR package](https://aur.archlinux.org/packages/headset-battery-indicator-git) by [@segarra99](https://github.com/segarra99).

---

### Option 4: From Source

1. **Install system dependencies:**

   ```bash
   # Fedora:
   sudo dnf install headsetcontrol python3-pyside6

   # Debian/Ubuntu:
   sudo apt install headsetcontrol python3-pyside6
   ```

2. **Clone and install:**

   ```bash
   git clone https://github.com/ruflas/headset-battery-indicator.git
   cd headset-battery-indicator
   pip install .
   ```

3. **Run:**
   ```bash
   headset-battery-indicator
   # or
   python -m headset_battery_indicator
   ```

---

## ⚙️ Usage

Once launched, the indicator appears in your system tray.

### Right-Click Menu

Right-clicking the tray icon gives you:

- **Device name and current status** (read-only info)
- **Preferences** — opens the configuration dialog
- **Notify on low battery** — toggle low-battery alerts
- **LED, Sidetone, ChatMix, Auto-Off** — direct device controls

![Screenshot of the context menu](screenshot2.png)

### Preferences Dialog

Open via the tray menu → **Preferences**. From here you can configure:

- Icon fill and border colors (color picker or `#RRGGBB` hex input)
- Battery icon orientation (horizontal / vertical)
- Icon zoom/scale
- Percentage text overlay
- Notification threshold (5–95%)
- Poll interval (10–300 seconds)
- **When disconnected** — choose between empty battery (default), error/X icon, or hiding the tray icon
- **Language** — select UI language; Spanish and English included (restart required)

All settings take effect immediately and are saved automatically.

---

## 🧠 Command-Line Options

| Option | Description |
|---|---|
| `-h`, `--help` | Show help message and exit |
| `-debug` | Enable interactive debug mode with live log output |

Example:
```bash
./Headset_Battery_Indicator-*.AppImage -debug
```

In debug mode, available commands include `setIcon 75`, `setIcon 100 charging`, `notification`, `update`, `mockon`, `mockoff`, `resume`, and `exit`.

---

## 🔄 Autostart

To run the indicator automatically on login:

1. Open **System Settings**.
2. Go to **Startup and Shutdown → Autostart** (KDE) or **Startup Applications** (GNOME/XFCE).
3. Add a new entry:
   - **AppImage:** `/full/path/to/Headset_Battery_Indicator-*.AppImage`
   - **Source install:** `headset-battery-indicator`

---

## 🔧 Troubleshooting

### "HeadsetControl binary not found"

Install `headsetcontrol` and verify it works before launching the indicator:

```bash
headsetcontrol -b
```

Installation by distro:

- **Fedora / RHEL:** `sudo dnf install headsetcontrol`
- **Debian / Ubuntu:** `sudo apt install headsetcontrol`
- **Manual:** see the [HeadsetControl releases page](https://github.com/Sapd/HeadsetControl/releases)

---

### Tray icon does not appear

| Desktop Environment | Fix |
|---|---|
| **GNOME** | Install [AppIndicator extension](https://extensions.gnome.org/extension/615/appindicator-support/) |
| **KDE Plasma** | Works out of the box |
| **XFCE / Cinnamon** | Works out of the box |

Also make sure `QT_QPA_PLATFORM` is not set to `offscreen`.

---

### USB permission denied / headset not detected

headsetcontrol needs USB device access. Install the udev rules:

```bash
sudo curl -o /etc/udev/rules.d/70-headsetcontrol.rules \
  https://raw.githubusercontent.com/Sapd/HeadsetControl/master/udev/70-headsetcontrol.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Then re-plug the headset.

---

### Debugging

Launch with `-debug` for live log output and an interactive console:

```bash
# AppImage:
./Headset_Battery_Indicator-*.AppImage -debug

# Source install:
python -m headset_battery_indicator -debug
```

The rotating log file is always written to:

```
~/.local/share/HeadsetBatteryIndicator/logs/app.log
```
