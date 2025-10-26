# 🎧 Headset Battery Indicator

A simple, lightweight Python script that displays the battery level of your wireless headset in your Linux system tray.

It uses **PySide6 (Qt)** for the tray icon, making it compatible with most modern desktop environments such as **KDE Plasma**, **GNOME**, **XFCE**, and **Cinnamon**.


![Screenshot of the tray icon](screenshot.png)
---

## ⭐ Core Dependency: HeadsetControl

This script **does not work on its own** — it is a graphical front-end that relies entirely on the **[HeadsetControl](https://github.com/Sapd/HeadsetControl)** utility.

You **must** install `headsetcontrol` for this indicator to function.  
All credit for hardware communication and device support goes to the [Sapd/HeadsetControl](https://github.com/Sapd/HeadsetControl) project.

---

## ✨ Features

- Displays a dynamic tray icon that reflects the current battery level.
- Shows a charging icon when the device is plugged in.
- Updates automatically every 60 seconds.
- Displays the device name (from `headsetcontrol`) in the tooltip.
- Extremely low resource usage.

---

## 🧩 Requirements

1. **[HeadsetControl](https://github.com/Sapd/HeadsetControl)** (Required)
2. **Python 3**
3. **PySide6** (Qt for Python)

---

## ⚙️ Installation

### 1. Install Dependencies

Make sure you have `headsetcontrol` and `python3-pyside6` installed via your package manager.

```bash
# On Fedora:
sudo dnf install headsetcontrol python3-pyside6

# On Debian/Ubuntu:
# (headsetcontrol may need to be built from source if not in your repo)
sudo apt install python3-pyside6 headsetcontrol
```

### 2. Clone the Repository

```bash
git clone https://github.com/ruflas/headset-battery-indicator.git
cd headset-battery-indicator
```

### 3. Make the Script Executable

```bash
chmod +x headsetcontrol_tray.py
```

---

## ▶️ Usage

Run the script directly from your terminal:

```bash
python3 headsetcontrol_tray.py
```

Optionally, you can add it to your **startup applications** so it runs automatically when you log in.
