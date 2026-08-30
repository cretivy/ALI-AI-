import subprocess

def open_app(app_name):
    """Launch macOS application by name"""
    try:
        # Standardize app names
        mapping = {
            "telegram": "Telegram",
            "safari": "Safari",
            "chrome": "Google Chrome",
            "google chrome": "Google Chrome",
            "spotify": "Spotify",
            "finder": "Finder",
            "vs code": "Visual Studio Code",
            "vscode": "Visual Studio Code",
            "calculator": "Calculator",
            "notes": "Notes"
        }
        target_app = mapping.get(app_name.lower(), app_name)
        subprocess.run(["open", "-a", target_app], check=True)
        return True, f"{target_app} muvaffaqiyatli ochildi."
    except Exception as e:
        return False, f"Ilovani ochishda xatolik: {e}"

def set_volume(action):
    """Control macOS system volume via osascript"""
    try:
        if action == "volume_up":
            cmd = "set volume output volume ((output volume of (get volume settings)) + 15)"
        elif action == "volume_down":
            cmd = "set volume output volume ((output volume of (get volume settings)) - 15)"
        elif action == "mute":
            cmd = "set volume with output muted"
        elif action == "unmute":
            cmd = "set volume without output muted"
        else:
            return False, "Noma'lum ovoz sozlamasi."

        subprocess.run(["osascript", "-e", cmd], check=True)
        return True, "Ovoz sozlandi."
    except Exception as e:
        return False, f"Ovozni sozlashda xatolik: {e}"

def notify_mac(title, message):
    """Display macOS Native Desktop Notification"""
    try:
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script])
    except Exception:
        pass
