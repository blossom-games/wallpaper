import os
import sys
import time
import math
import random
import ctypes
import platform
import datetime
import subprocess
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# PyStray & Tkinter for GUI & System Tray
try:
    import pystray
    from pystray import MenuItem as item
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False

import tkinter as tk
from tkinter import ttk, messagebox

# ==========================================
# DEFAULT CONFIGURATION
# ==========================================
DEFAULT_CONFIG = {
    "api_key": "626def276d159246a1f82a8d83a486fe",
    "city": "San Jose",
    "update_interval_mins": 15,
    "units": "imperial",  # 'imperial' (°F) or 'metric' (°C)
    "show_overlay": True,
    "randomize_multi_images": True,
}

CONFIG_DIR = Path.home() / ".config" / "weather_wallpaper"
CONFIG_FILE = CONFIG_DIR / "config.json"
WALLPAPER_DIR = Path(__file__).parent / "wallpapers"
PROCESSED_DIR = CONFIG_DIR / "processed_wallpapers"

# ==========================================
# CONFIG HELPER FUNCTIONS
# ==========================================
def load_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            import json
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                return config
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        import json
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"[Config Error] Could not save config: {e}")

# Global state
config = load_config()

# ==========================================
# WEATHER & TIME COMPUTATION
# ==========================================
def get_current_location():
    try:
        res = requests.get("https://ipapi.co/json/", timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get("city", "San Jose")
    except Exception:
        pass
    return "San Jose"

def get_time_period(sunrise_ts, sunset_ts):
    now_ts = time.time()
    one_hour_seconds = 3600

    if not sunrise_ts or not sunset_ts:
        hour = datetime.datetime.now().hour
        if 5 <= hour <= 7:
            return "sunrise"
        elif 8 <= hour <= 16:
            return "day"
        elif 17 <= hour <= 19:
            return "sunset"
        else:
            return "night"

    if abs(now_ts - sunrise_ts) <= one_hour_seconds:
        return "sunrise"
    if abs(now_ts - sunset_ts) <= one_hour_seconds:
        return "sunset"
    if (sunrise_ts + one_hour_seconds) < now_ts < (sunset_ts - one_hour_seconds):
        return "day"
    return "night"

def get_weather_data(city, api_key, units="imperial"):
    unit_param = "imperial" if units == "imperial" else "metric"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units={unit_param}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()

        if res.status_code != 200:
            print(f"[API Error] {data.get('message', 'Failed to fetch weather')}")
            return {
                "condition": "clear",
                "desc": "Clear Sky",
                "temp": 72 if units == "imperial" else 22,
                "high": 78 if units == "imperial" else 25,
                "low": 60 if units == "imperial" else 15,
                "sunrise_ts": None,
                "sunset_ts": None,
            }

        main_cond = data["weather"][0]["main"].lower()
        desc = data["weather"][0]["description"].title()
        temp = round(data["main"]["temp"])
        high = round(data["main"]["temp_max"])
        low = round(data["main"]["temp_min"])

        sys_data = data.get("sys", {})
        sunrise_ts = sys_data.get("sunrise")
        sunset_ts = sys_data.get("sunset")

        if any(term in main_cond for term in ["clear", "sun"]):
            condition = "clear"
        elif any(term in main_cond for term in ["cloud", "mist", "fog", "haze"]):
            condition = "cloudy"
        elif any(term in main_cond for term in ["rain", "drizzle", "thunder", "snow"]):
            condition = "rainy"
        else:
            condition = "clear"

        return {
            "condition": condition,
            "desc": desc,
            "temp": temp,
            "high": high,
            "low": low,
            "sunrise_ts": sunrise_ts,
            "sunset_ts": sunset_ts,
        }
    except Exception as e:
        print(f"[Network Error] {e}")
        return {
            "condition": "clear",
            "desc": "Clear",
            "temp": 70,
            "high": 75,
            "low": 65,
            "sunrise_ts": None,
            "sunset_ts": None,
        }

# ==========================================
# WALLPAPER SELECTION & IMAGE OVERLAY
# ==========================================
def select_wallpaper_file(condition, time_period, allow_random=True):
    WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)

    if time_period == "sunrise":
        base_targets = ["sunrise"]
    elif time_period == "sunset":
        base_targets = ["sunset"]
    else:
        if time_period == "day":
            if condition == "cloudy":
                base_targets = ["cloudy", "cloudy_day"]
            elif condition == "rainy":
                base_targets = ["rainy", "rainy_day"]
            else:
                base_targets = ["clearday", "clear_day"]
        else:
            if condition == "cloudy":
                base_targets = ["cloudynight", "cloudy_night"]
            elif condition == "rainy":
                base_targets = ["rainynight", "rainy_night"]
            else:
                base_targets = ["clearnight", "clear_night"]

    matching_files = []
    all_files = [f for f in WALLPAPER_DIR.iterdir() if f.suffix.lower() in [".png", ".jpg", ".jpeg"]]

    for target in base_targets:
        for f in all_files:
            if f.stem.lower() == target or (allow_random and f.stem.lower().startswith(f"{target}_")):
                matching_files.append(f)

    if matching_files:
        return random.choice(matching_files)

    # Fallback search
    for target in base_targets:
        for f in all_files:
            if target in f.stem.lower():
                matching_files.append(f)

    if matching_files:
        return random.choice(matching_files)

    return all_files[0] if all_files else None

def create_weather_overlay(image_path, weather_info, city, units_symbol):
    """Draws a modern weather badge/overlay onto the bottom corner of the image."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with Image.open(image_path) as img:
            img = img.convert("RGBA")
            width, height = img.size

            # Create an overlay layer for subtle translucent glassmorphism box
            overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)

            text_main = f"{city} • {weather_info['temp']}°{units_symbol}"
            text_sub = f"{weather_info['desc']} | H: {weather_info['high']}° L: {weather_info['low']}°"

            # Determine font size dynamically based on image resolution
            font_size_main = max(20, int(height * 0.035))
            font_size_sub = max(14, int(height * 0.020))

            try:
                # Standard cross-platform font loading
                if platform.system() == "Windows":
                    font_main = ImageFont.truetype("arial.ttf", font_size_main)
                    font_sub = ImageFont.truetype("arial.ttf", font_size_sub)
                elif platform.system() == "Darwin":
                    font_main = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size_main)
                    font_sub = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size_sub)
                else:
                    font_main = ImageFont.truetype("DejaVuSans.ttf", font_size_main)
                    font_sub = ImageFont.truetype("DejaVuSans.ttf", font_size_sub)
            except Exception:
                font_main = ImageFont.load_default()
                font_sub = ImageFont.load_default()

            # Measure text dimensions
            bbox_main = draw.textbbox((0, 0), text_main, font=font_main)
            bbox_sub = draw.textbbox((0, 0), text_sub, font=font_sub)

            box_w = max(bbox_main[2] - bbox_main[0], bbox_sub[2] - bbox_sub[0]) + 40
            box_h = (bbox_main[3] - bbox_main[1]) + (bbox_sub[3] - bbox_sub[1]) + 35

            # Position in bottom-right corner with margin
            margin_right = int(width * 0.04)
            margin_bottom = int(height * 0.05)

            x2 = width - margin_right
            y2 = height - margin_bottom
            x1 = x2 - box_w
            y1 = y2 - box_h

            # Draw rounded translucent rectangle
            corner_radius = 15
            draw.rounded_rectangle(
                [x1, y1, x2, y2],
                radius=corner_radius,
                fill=(0, 0, 0, 130),
                outline=(255, 255, 255, 60),
                width=1,
            )

            # Draw text inside box
            draw.text((x1 + 20, y1 + 12), text_main, fill=(255, 255, 255, 240), font=font_main)
            draw.text((x1 + 20, y1 + 18 + (bbox_main[3] - bbox_main[1])), text_sub, fill=(220, 220, 220, 200), font=font_sub)

            # Composite text overlay onto original image
            processed_img = Image.alpha_composite(img, overlay)
            out_path = PROCESSED_DIR / "current_wallpaper.png"
            processed_img.convert("RGB").save(out_path, "PNG")
            return out_path

    except Exception as e:
        print(f"[Overlay Error] Failed to generate overlay: {e}")
        return image_path

# ==========================================
# CROSS-PLATFORM SYSTEM WALLPAPER SETTER
# ==========================================
def set_system_wallpaper(image_path):
    abs_path = str(image_path.resolve())
    sys_name = platform.system()

    try:
        if sys_name == "Windows":
            ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
            print("[System] Windows desktop background updated.")

        elif sys_name == "Darwin":  # macOS
            script = f'tell application "Finder" to set desktop picture to POSIX file "{abs_path}"'
            subprocess.run(["osascript", "-e", script], check=True)
            print("[System] macOS desktop background updated.")

        elif sys_name == "Linux":
            # Supports GNOME, KDE, XFCE
            desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

            if "gnome" in desktop_env or "ubuntu" in desktop_env or "unity" in desktop_env:
                subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"file://{abs_path}"])
                subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", f"file://{abs_path}"])
            elif "kde" in desktop_env:
                js_script = f"""
                var allDesktops = desktops();
                for (i=0;i<allDesktops.length;i++) {{
                    d = allDesktops[i];
                    d.wallpaperPlugin = "org.kde.image";
                    d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
                    d.writeConfig("Image", "file://{abs_path}");
                }}
                """
                subprocess.run(["qdbus", "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", js_script])
            elif "xfce" in desktop_env:
                subprocess.run(["xfconf-query", "-c", "xfce4-desktop", "-p", "/backdrop/screen0/monitor0/workspace0/last-image", "-s", abs_path])
            else:
                # Default fallback for Linux
                subprocess.run(["feh", "--bg-fill", abs_path])
            print("[System] Linux desktop background updated.")

    except Exception as e:
        print(f"[Wallpaper System Error] Could not set background: {e}")

# ==========================================
# CORE WORKFLOW UPDATE
# ==========================================
def update_wallpaper():
    global config
    city = config["city"].strip() if config["city"].strip() else get_current_location()
    api_key = config["api_key"]
    units = config.get("units", "imperial")

    weather = get_weather_data(city, api_key, units)
    time_period = get_time_period(weather["sunrise_ts"], weather["sunset_ts"])

    selected_image = select_wallpaper_file(
        weather["condition"],
        time_period,
        allow_random=config.get("randomize_multi_images", True)
    )

    if not selected_image:
        print("[Error] No wallpapers found in the wallpapers directory!")
        return

    units_symbol = "F" if units == "imperial" else "C"

    if config.get("show_overlay", True):
        final_image = create_weather_overlay(selected_image, weather, city, units_symbol)
    else:
        final_image = selected_image

    set_system_wallpaper(final_image)

    now = datetime.datetime.now().strftime("%I:%M %p")
    print(f"[{now}] Applied wallpaper: {selected_image.name} for {city} ({weather['desc']}, {weather['temp']}°{units_symbol})")

# ==========================================
# SETTINGS GUI (Tkinter)
# ==========================================
def open_settings_window():
    root = tk.Tk()
    root.title("Dynamic Weather Wallpaper Settings")
    root.geometry("450x420")
    root.resizable(False, False)

    # Styling
    style = ttk.Style(root)
    style.theme_use("clam")

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    # Title
    ttk.Label(frame, text="Dynamic Wallpaper Preferences", font=("Helvetica", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="w")

    # API Key
    ttk.Label(frame, text="OpenWeatherMap API Key:").grid(row=1, column=0, sticky="w", pady=5)
    api_entry = ttk.Entry(frame, width=35)
    api_entry.insert(0, config.get("api_key", ""))
    api_entry.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))

    # City
    ttk.Label(frame, text="City Name (leave blank to auto-detect):").grid(row=3, column=0, sticky="w", pady=5)
    city_entry = ttk.Entry(frame, width=35)
    city_entry.insert(0, config.get("city", ""))
    city_entry.grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 10))

    # Units Selection
    ttk.Label(frame, text="Temperature Units:").grid(row=5, column=0, sticky="w", pady=5)
    units_var = tk.StringVar(value=config.get("units", "imperial"))
    units_frame = ttk.Frame(frame)
    units_frame.grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 10))
    ttk.Radiobutton(units_frame, text="Fahrenheit (°F)", variable=units_var, value="imperial").pack(side=tk.LEFT, padx=(0, 15))
    ttk.Radiobutton(units_frame, text="Celsius (°C)", variable=units_var, value="metric").pack(side=tk.LEFT)

    # Checkbox Options
    overlay_var = tk.BooleanVar(value=config.get("show_overlay", True))
    random_var = tk.BooleanVar(value=config.get("randomize_multi_images", True))

    ttk.Checkbutton(frame, text="Display Weather & Temp Overlay Badge", variable=overlay_var).grid(row=7, column=0, columnspan=2, sticky="w", pady=5)
    ttk.Checkbutton(frame, text="Randomize when multiple variants exist", variable=random_var).grid(row=8, column=0, columnspan=2, sticky="w", pady=5)

    def save_and_close():
        global config
        config["api_key"] = api_entry.get().strip()
        config["city"] = city_entry.get().strip()
        config["units"] = units_var.get()
        config["show_overlay"] = overlay_var.get()
        config["randomize_multi_images"] = random_var.get()

        save_config(config)
        update_wallpaper()
        messagebox.showinfo("Success", "Settings saved and wallpaper updated!")
        root.destroy()

    btn_frame = ttk.Frame(frame)
    btn_frame.grid(row=9, column=0, columnspan=2, pady=(20, 0), sticky="e")

    ttk.Button(btn_frame, text="Cancel", command=root.destroy).pack(side=tk.LEFT, padx=(0, 10))
    ttk.Button(btn_frame, text="Save & Apply", command=save_and_close).pack(side=tk.LEFT)

    root.mainloop()

# ==========================================
# APPLICATION ENTRYPOINT & TRAY ICON
# ==========================================
def main():
    print("=========================================")
    print(" Cross-Platform Weather Wallpaper Service")
    print("=========================================")

    # Initial wallpaper update
    update_wallpaper()

    # System Tray Integration if pystray is installed
    if HAS_PYSTRAY:
        # Create a simple tray icon
        icon_image = Image.new("RGB", (64, 64), color=(73, 109, 137))
        draw = ImageDraw.Draw(icon_image)
        draw.ellipse((16, 16, 48, 48), fill=(255, 235, 59))

        def on_update_click(icon, item):
            update_wallpaper()

        def on_settings_click(icon, item):
            open_settings_window()

        def on_exit_click(icon, item):
            icon.stop()
            sys.exit(0)

        menu = pystray.Menu(
            item("Force Update Wallpaper", on_update_click),
            item("Preferences / Settings", on_settings_click),
            pystray.Menu.SEPARATOR,
            item("Exit", on_exit_click),
        )

        icon = pystray.Icon("WeatherWallpaper", icon_image, "Weather Wallpaper", menu)

        # Run periodic background timer in a non-blocking loop
        def loop_timer():
            while True:
                interval_secs = max(5, config.get("update_interval_mins", 15)) * 60
                time.sleep(interval_secs)
                update_wallpaper()

        import threading
        t = threading.Thread(target=loop_timer, daemon=True)
        t.start()

        icon.run()
    else:
        # Fallback loop without system tray
        print("[System Tray] 'pystray' library not installed. Running background service loop...")
        while True:
            interval_secs = max(5, config.get("update_interval_mins", 15)) * 60
            time.sleep(interval_secs)
            update_wallpaper()

if __name__ == "__main__":
    main()