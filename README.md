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

* **Dynamic Tray Icon:** Displays battery level and charging status at a glance.
* **Configurable Notifications:** Get a desktop notification (and a headset sound!) when your battery drops below a level you choose.
* **Full Context Menu:** Right-click the icon to:
    * See the connected device name and status.
    * Enable or disable low-battery notifications.
    * Set the notification threshold (10%, 20%, 30%, etc.).
* **Persistent Settings:** Remembers your notification preferences after a restart.
* **Tooltip Info:** Hover over the icon to see the device name and battery percentage.
* **Extremely low resource usage.**

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

### Configuration (Right-Click Menu)

This indicator is now fully configurable. **Right-click the tray icon** at any time to:

* **Enable/Disable Notifications:** Toggle the "Notify on low battery" option.
* **Set Notification Level:** Open the "Set Notification Level" submenu and choose the percentage at which you want to be warned.

Your preferences are saved automatically and will be reloaded the next time you start the script.
![Screenshot of configuration](screenshot2.png)
### Command-line Arguments

You can also launch the script with these arguments:

* `-h` or `--help`: Shows a help message with all available options and exits.
* `-debug`: Launches in interactive debug mode. This allows you to type commands directly into the terminal (like `notification` or `setIcon battery-100-symbolic`) to test the script's behavior in real-time.