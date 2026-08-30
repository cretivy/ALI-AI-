import os
import time
import subprocess
from actions.mac_actions import open_app, notify_mac

def handle_telegram_action(recipient=None, message=None):
    """
    Handles Telegram interactions on macOS:
    1. Opens Telegram Desktop app.
    2. If recipient/message specified, resolves contact or prepares message.
    """
    # 1. Open Telegram
    success, msg = open_app("Telegram")
    if not success:
        return False, msg

    if not recipient and not message:
        return True, "Telegram ilovasi ochildi."

    time.sleep(0.8) # Allow Telegram window to focus

    # If message is provided, put it into macOS clipboard and paste into Telegram search/chat using osascript
    if message:
        try:
            # Copy text to macOS clipboard
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            process.communicate(message.encode('utf-8'))

            # AppleScript to focus Telegram and paste (Cmd+V) or search
            applescript = """
            tell application "Telegram" to activate
            delay 1.5
            tell application "System Events"
                -- Reset any active focus by pressing Escape
                key code 53
                delay 0.3
                -- Search contact or chat if recipient is specified
                keystroke "f" using {command down}
                delay 0.5
                """
            if recipient:
                # Type recipient name, wait for search results, press Enter to open chat
                applescript += f'keystroke "{recipient}"\n delay 1.2\n key code 36\n delay 0.8\n'
            
            # Paste message into chat box and press Enter to send
            applescript += """
                keystroke "v" using {command down}
                delay 0.5
                key code 36
            end tell
            """
            subprocess.run(["osascript", "-e", applescript], check=False)
            notify_mac("Jarvis Telegram", f"{recipient or 'Chat'}ga xabar yuborildi!")
            friend = recipient or "do'stingiz"
            return True, f"Telegramda {friend}ga xabar muvaffaqiyatli yuborildi!"
        except Exception as e:
            return False, f"Telegram xabar tayyorlashda xatolik: {e}"

    return True, "Telegram ochildi."
