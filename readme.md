# 🌤️ Cross-Platform Dynamic Weather Wallpaper

A lightweight cross-platform Python application that dynamically updates your desktop background based on your local weather and the position of the sun (sunrise, day, sunset, night). It includes an automatic glassmorphic desktop weather overlay badge, system tray control, and multi-image randomization.

---

## 🌟 Features

* **Cross-Platform Support**: Native support for **Windows 10/11**, **macOS**, and major Linux desktop environments (**GNOME**, **KDE Plasma**, **XFCE**).
* **Weather & Time Aware**: Automatically shifts backgrounds for `Sunrise`, `Clear Day`, `Cloudy Day`, `Rainy Day`, `Sunset`, `Clear Night`, `Cloudy Night`, and `Rainy Night`.
* **Subtle Glassmorphic Overlay**: Draws a slick, modern weather badge displaying the city, current temperature, description, and high/low onto the corner of your wallpaper.
* **System Tray Application**: Sits in your system menu bar or tray with a quick-access menu to force updates, open preferences, or exit.
* **Preferences GUI**: Easily toggle units (°F / °C), update location, set OpenWeatherMap API keys, or disable overlays.
* **Multi-Variant Support**: Put multiple wallpapers for a single weather condition (e.g., `clearday_1.jpg`, `clearday_2.jpg`), and the app will randomize them.

---

## 📋 Prerequisites & Installation

### 1. Install Python
Ensure **Python 3.8 or newer** is installed on your system.
* **Windows**: Download from [python.org](https://www.python.org/) *(Check "Add Python to PATH" during installation)*.
* **macOS**: `brew install python`
* **Linux**: `sudo apt install python3 python3-pip python3-tk`

### 2. Install Required Packages
Open your terminal or command prompt and run:

```bash
pip install requests pillow pystray
```

*(Note for Linux users: You may need `python3-tk` installed via your distro's package manager for the settings GUI window).*

---

## 📁 Wallpaper Folder Setup

Create a folder named `wallpapers` in the same directory as `dynamic_wallpaper_app.py`.

Place your images in the `wallpapers/` folder using any of the following standard naming conventions (supports `.png`, `.jpg`, `.jpeg`):

| File Name | Trigger Condition |
| :--- | :--- |
| `sunrise.png` | Within 1 hour before/after local sunrise time |
| `sunset.png` | Within 1 hour before/after local sunset time |
| `clearday.png` | Clear skies during daytime |
| `cloudy.png` or `cloudy_day.png` | Clouds, fog, or mist during daytime |
| `rainy.png` or `rainy_day.png` | Rain, snow, or thunderstorm during daytime |
| `clearnight.png` | Clear skies at night |
| `cloudynight.png` | Clouds at night |
| `rainynight.png` | Rain or storms at night |

> 💡 **Tip:** To randomize between multiple wallpapers for the same condition, add numbers after an underscore! For example: `clearday_1.jpg`, `clearday_2.jpg`, `clearday_3.jpg`.

---

## 🚀 Running the Application

### Standard Run (Terminal / Command Prompt)

```bash
python dynamic_wallpaper_app.py
```

---

## ⚙️ How to Run Automatically on Boot

### 🪟 Windows (Silent Background Service)

To run the app silently without a black command window appearing:

1. Rename `dynamic_wallpaper_app.py` to `dynamic_wallpaper_app.pyw` (or run it using `pythonw`).
2. Press **`Win + R`**, type **`shell:startup`**, and hit **Enter**.
3. Create a shortcut in this startup folder with the location:
   ```cmd
   pythonw "C:\Path\To\Your\dynamic_wallpaper_app.pyw"
   ```

---

### 🍎 macOS (Run at Login)

1. Open **System Settings** > **General** > **Login Items**.
2. Click the **+** button under **Open at Login**.
3. Alternatively, wrap the execution command inside an **Automator Application** and set it as a login item.

---

### 🐧 Linux (Autostart `.desktop` file)

1. Create a file at `~/.config/autostart/weather_wallpaper.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Weather Wallpaper
Exec=python3 /path/to/dynamic_wallpaper_app.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
```

---

## 🔧 Configuration & API Key

By default, the app uses built-in location auto-detection via IP geolocation.

To set your own **OpenWeatherMap API Key**, change city overrides, or switch between Imperial (°F) and Metric (°C):

1. Right-click the **System Tray Icon** (near your system clock).
2. Click **Preferences / Settings**.
3. Enter your preferences and click **Save & Apply**.

Your settings are saved automatically in `~/.config/weather_wallpaper/config.json`.