import subprocess
import requests
import re
import urllib.parse
import os

def open_application(app_name: str) -> str:
    """
    Launches a macOS application by name.
    
    Args:
        app_name: The name of the application to open (e.g., 'Safari', 'Google Chrome', 'Spotify', 'Finder', 'Telegram', 'Notes', etc.)
    
    Returns:
        A message indicating success or failure.
    """
    print(f"🔧 Jarvis: '{app_name}' ilovasini ochmoqda...")
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
        return f"{target_app} muvaffaqiyatli ochildi."
    except Exception as e:
        return f"Ilovani ochishda xatolik yuz berdi: {e}"

def run_applescript(script_code: str) -> str:
    """
    Executes an AppleScript on macOS. Use this tool to automate macOS settings (volume, brightness, mute, sleep, notifications)
    or to control GUI elements of active applications.
    
    Args:
        script_code: The AppleScript code to execute.
        
    Returns:
        The standard output or error from executing the AppleScript.
    """
    print("🔧 Jarvis: AppleScript tizim buyrug'ini ishga tushirmoqda...")
    try:
        proc = subprocess.run(["osascript"], input=script_code, capture_output=True, text=True, timeout=15)
        if proc.returncode == 0:
            return f"Muvaffaqiyatli bajarildi. Natija: {proc.stdout.strip() if proc.stdout else 'Bajarildi (javobsiz)'}"
        else:
            return f"AppleScript xatoligi: {proc.stderr.strip()}"
    except Exception as e:
        return f"AppleScript ishga tushirishda xatolik: {e}"

def run_bash_command(command: str) -> str:
    """
    Runs a shell command in the macOS terminal. Use this to search files, list directories, 
    check network/system status, or execute terminal utilities.
    
    Args:
        command: The shell command to run.
        
    Returns:
        The standard output or error from executing the command.
    """
    print(f"🔧 Jarvis: Terminal buyrug'ini ishga tushirmoqda: {command}")
    try:
        proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=20)
        stdout = proc.stdout.strip() if proc.stdout else ""
        stderr = proc.stderr.strip() if proc.stderr else ""
        
        # Limit response length to prevent overloading context
        max_chars = 3000
        if len(stdout) > max_chars:
            stdout = stdout[:max_chars] + "\n... (Natija juda uzun bo'lgani uchun qisqartirildi)"
            
        result = []
        if stdout:
            result.append(f"stdout:\n{stdout}")
        if stderr:
            result.append(f"stderr:\n{stderr}")
            
        if not result:
            return "Command executed successfully with no output."
        return "\n".join(result)
    except Exception as e:
        return f"Command execution error: {e}"

def search_web(query: str) -> str:
    """
    Searches the web using DuckDuckGo HTML search and returns titles, links, and text snippets of matching pages.
    Use this when the user asks for real-time information, weather, news, or general facts.
    
    Args:
        query: The search terms.
        
    Returns:
        A list of search results with titles, links, and snippets.
    """
    print(f"🔧 Jarvis: Internetdan qidirmoqda: '{query}'...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return f"Qidiruvda xatolik yuz berdi (Status code: {r.status_code})"
        
        # Find results matching DuckDuckGo HTML layout
        titles_links = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', r.text)
        snippets = re.findall(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', r.text, re.DOTALL)
        
        results = []
        for i, (link, title) in enumerate(titles_links[:5]):
            title_clean = re.sub(r'<[^>]+>', '', title).strip()
            title_clean = title_clean.replace("&#x27;", "'").replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            
            snippet_clean = ""
            if i < len(snippets):
                snippet_clean = re.sub(r'<[^>]+>', '', snippets[i]).strip()
                snippet_clean = snippet_clean.replace("&#x27;", "'").replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            
            if "uddg=" in link:
                parsed_link = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])
            elif link.startswith("//"):
                parsed_link = "https:" + link
            else:
                parsed_link = link
                
            results.append(f"{i+1}. {title_clean}\n   Link: {parsed_link}\n   Info: {snippet_clean}")
            
        return "\n\n".join(results) if results else "Mavzuga doir hech narsa topilmadi."
    except Exception as e:
        return f"Internet qidiruvida xatolik: {e}"

def read_webpage_content(url: str) -> str:
    """
    Fetches the HTML of a webpage and extracts its text content. Use this to read details from a link.
    
    Args:
        url: The URL to scrape.
        
    Returns:
        Text content of the webpage.
    """
    print(f"🔧 Jarvis: Veb sahifa tarkibini o'qimoqda: {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code != 200:
            return f"Saytni o'qib bo'lmadi (Status: {r.status_code})"
        
        # Remove script and style elements
        html = re.sub(r'<(script|style).*?>.*?</\1>', '', r.text, flags=re.DOTALL|re.IGNORECASE)
        # Remove comments
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        # Strip all HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit return content to avoid context overflow
        return text[:4000]
    except Exception as e:
        return f"Veb sahifani o'qishda xatolik yuz berdi: {e}"

def read_file_content(filepath: str) -> str:
    """
    Reads the full text contents of a file on the local computer.
    
    Args:
        filepath: Absolute path to the file.
        
    Returns:
        The content of the file or error message.
    """
    print(f"🔧 Jarvis: Faylni o'qimoqda: {filepath}...")
    try:
        expanded_path = os.path.expanduser(filepath)
        if not os.path.exists(expanded_path):
            return f"Xato: Fayl topilmadi ({filepath})"
        
        with open(expanded_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        if len(content) > 4000:
            content = content[:4000] + "\n... (Fayl juda uzun bo'lgani uchun qisqartirildi)"
        return content
    except Exception as e:
        return f"Faylni o'qishda xatolik yuz berdi: {e}"

def write_file_content(filepath: str, content: str) -> str:
    """
    Writes or overwrites text content to a local file.
    
    Args:
        filepath: Absolute path to the file.
        content: The text content to write.
        
    Returns:
        Success or failure message.
    """
    print(f"🔧 Jarvis: Faylga yozmoqda: {filepath}...")
    try:
        expanded_path = os.path.expanduser(filepath)
        # Ensure directory exists
        if os.path.dirname(expanded_path):
            os.makedirs(os.path.dirname(expanded_path), exist_ok=True)
        
        with open(expanded_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Fayl muvaffaqiyatli yozildi: {filepath}"
    except Exception as e:
        return f"Faylga yozishda xatolik yuz berdi: {e}"

def play_youtube(query: str) -> str:
    """
    Searches and automatically plays a YouTube video, music, song, or movie in the default web browser.
    Use this when the user wants to play a song, music, video, or movie on YouTube.
    
    Args:
        query: The name of the video, song, or movie to search and play.
        
    Returns:
        A message indicating success or failure.
    """
    print(f"🔧 Jarvis: YouTubedan ijro etilmoqda: '{query}'...")
    try:
        from actions.youtube import play_youtube as play
        success, msg = play(query)
        return msg
    except Exception as e:
        return f"YouTube ijrosida xatolik: {e}"

def send_telegram_message(recipient: str, message: str) -> str:
    """
    Sends a message to a contact or friend on Telegram Desktop.
    Use this when the user wants to send a Telegram message to someone.
    
    Args:
        recipient: The name of the recipient (contact name or username).
        message: The text message to send.
        
    Returns:
        A message indicating success or failure.
    """
    print(f"🔧 Jarvis: Telegramdan xabar yuborilmoqda: '{recipient}'ga...")
    try:
        from actions.telegram import handle_telegram_action
        success, msg = handle_telegram_action(recipient, message)
        return msg
    except Exception as e:
        return f"Telegramda xabar yuborishda xatolik: {e}"

def lock_mac_screen() -> str:
    """
    Locks the macOS screen instantly, putting the computer to secure lock.
    Use this when the user wants to lock the screen, lock their Macbook, or secure the display.
    """
    print("🔧 Jarvis: Macbook ekranini bloklamoqda...")
    try:
        # Lock screen keystroke via AppleScript (Ctrl + Cmd + Q)
        cmd = "osascript -e 'tell application \"System Events\" to keystroke \"q\" using {control down, command down}'"
        subprocess.run(cmd, shell=True, check=True)
        return "Macbook ekrani muvaffaqiyatli bloklandi."
    except Exception as e:
        # Fallback to displaysleepnow
        try:
            subprocess.run(["pmset", "displaysleepnow"], check=True)
            return "Macbook displeyi uyqu rejimiga o'tkazildi (bloklandi)."
        except Exception as ex:
            return f"Ekranni bloklashda xatolik: {e}"

def add_calendar_event(title: str, start_time: str, duration_minutes: int = 60) -> str:
    """
    Creates a new event in the macOS Calendar application.
    
    Args:
        title: The title/summary of the event.
        start_time: Start date and time in format 'YYYY-MM-DD HH:MM:SS'.
        duration_minutes: Duration of the event in minutes.
    """
    print(f"🔧 Jarvis: Kalendarga tadbir qo'shilmoqda: '{title}'...")
    try:
        from datetime import datetime, timedelta
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        # Generate safe AppleScript
        applescript = f"""
        tell application "Calendar"
            set start_date to (current date)
            set year of start_date to {start_dt.year}
            set month of start_date to {start_dt.month}
            set day of start_date to {start_dt.day}
            set hours of start_date to {start_dt.hour}
            set minutes of start_date to {start_dt.minute}
            set seconds of start_date to 0
            
            set end_date to (current date)
            set year of end_date to {end_dt.year}
            set month of end_date to {end_dt.month}
            set day of end_date to {end_dt.day}
            set hours of end_date to {end_dt.hour}
            set minutes of end_date to {end_dt.minute}
            set seconds of end_date to 0
            
            tell calendar 1
                make new event with properties {{summary: "{title}", start date: start_date, end date: end_date}}
            end tell
        end tell
        """
        subprocess.run(["osascript", "-e", applescript], check=True)
        return f"Tadbir '{title}' muvaffaqiyatli kalendarga qo'shildi: {start_time}"
    except Exception as e:
        return f"Kalendarga tadbir qo'shishda xatolik: {e}"

def get_calendar_events(date_str: str = "") -> str:
    """
    Lists all calendar events for a specific date.
    
    Args:
        date_str: The target date in format 'YYYY-MM-DD'. If empty, defaults to today.
    """
    print(f"🔧 Jarvis: Kalendar tadbirlari o'qilmoqda: {date_str or 'bugun'}...")
    try:
        from datetime import datetime
        if date_str:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            target_date = datetime.today()
            
        applescript = f"""
        tell application "Calendar"
            set start_date to (current date)
            set year of start_date to {target_date.year}
            set month of start_date to {target_date.month}
            set day of start_date to {target_date.day}
            set hours of start_date to 0
            set minutes of start_date to 0
            set seconds of start_date to 0
            
            set end_date to (current date)
            set year of end_date to {target_date.year}
            set month of end_date to {target_date.month}
            set day of end_date to {target_date.day}
            set hours of end_date to 23
            set minutes of end_date to 59
            set seconds of end_date to 59
            
            set out_list to ""
            repeat with a_cal in every calendar
                try
                    set day_events to (every event of a_cal whose start date is greater than or equal to start_date and start date is less than or equal to end_date)
                    repeat with an_event in day_events
                        set event_start to (start date of an_event)
                        set t_str to time string of event_start
                        set out_list to out_list & (summary of an_event) & " (" & t_str & ") " & linefeed
                    end repeat
                end try
            end repeat
            return out_list
        end tell
        """
        proc = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, check=True)
        result = proc.stdout.strip()
        if not result:
            return f"{date_str or 'bugun'} uchun hech qanday tadbir topilmadi."
        return f"{date_str or 'bugun'} uchun tadbirlar:\n{result}"
    except Exception as e:
        return f"Kalendar tadbirlarini o'qishda xatolik: {e}"

def add_reminder(title: str, due_date_time: str = "") -> str:
    """
    Creates a new reminder in the macOS Reminders application.
    
    Args:
        title: The reminder text.
        due_date_time: Optional due date and time in format 'YYYY-MM-DD HH:MM:SS'.
    """
    print(f"🔧 Jarvis: Eslatma qo'shilmoqda: '{title}'...")
    try:
        if due_date_time:
            from datetime import datetime
            dt = datetime.strptime(due_date_time, "%Y-%m-%d %H:%M:%S")
            applescript = f"""
            tell application "Reminders"
                set due_date to (current date)
                set year of due_date to {dt.year}
                set month of due_date to {dt.month}
                set day of due_date to {dt.day}
                set hours of due_date to {dt.hour}
                set minutes of due_date to {dt.minute}
                set seconds of due_date to 0
                
                tell list 1
                    make new reminder with properties {{name: "{title}", due date: due_date}}
                end tell
            end tell
            """
        else:
            applescript = f"""
            tell application "Reminders"
                tell list 1
                    make new reminder with properties {{name: "{title}"}}
                end tell
            end tell
            """
        subprocess.run(["osascript", "-e", applescript], check=True)
        due_str = f", muddati: {due_date_time}" if due_date_time else ""
        return f"Eslatma '{title}' muvaffaqiyatli qo'shildi{due_str}."
    except Exception as e:
        return f"Eslatma qo'shishda xatolik: {e}"

def get_reminders() -> str:
    """
    Lists all active reminders from the macOS Reminders application.
    """
    print("🔧 Jarvis: Eslatmalar ro'yxati o'qilmoqda...")
    try:
        applescript = """
        tell application "Reminders"
            set out_list to ""
            repeat with a_list in every list
                set active_reminders to (every reminder of a_list whose completed is false)
                repeat with a_rem in active_reminders
                    set out_list to out_list & (name of a_rem)
                    try
                        set out_list to out_list & " (Muddati: " & (short date string of (due date of a_rem)) & ")"
                    end try
                    set out_list to out_list & linefeed
                end repeat
            end repeat
            return out_list
        end tell
        """
        proc = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, check=True)
        result = proc.stdout.strip()
        if not result:
            return "Hech qanday faol eslatma topilmadi."
        return f"Faol eslatmalar:\n{result}"
    except Exception as e:
        return f"Eslatmalarni o'qishda xatolik: {e}"

def read_local_document(filepath: str) -> str:
    """
    Reads and extracts text from local files (PDF, Word DOCX/DOC, RTF, TXT, HTML).
    Use this when the user asks to read, analyze, or summarize a local document.
    
    Args:
        filepath: Absolute path to the document file.
    """
    print(f"🔧 Jarvis: Hujjat o'qilmoqda: {filepath}...")
    try:
        expanded_path = os.path.expanduser(filepath)
        if not os.path.exists(expanded_path):
            return f"Xatolik: Hujjat topilmadi: {filepath}"
            
        _, ext = os.path.splitext(expanded_path.lower())
        
        # 1. PDF files using pypdf
        if ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(expanded_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                    
        # 2. Word/RTF/HTML using macOS textutil utility
        elif ext in [".docx", ".doc", ".rtf", ".html", ".webarchive"]:
            cmd = ["textutil", "-convert", "txt", "-stdout", expanded_path]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            text = proc.stdout
            
        # 3. Plain Text or other readable files
        else:
            with open(expanded_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                
        text = text.strip()
        if not text:
            return f"Hujjat bo'sh yoki undan matn ajratib bo'lmadi: {filepath}"
            
        # Limit length to avoid blowing up the LLM context
        max_chars = 6000
        if len(text) > max_chars:
            return f"[Matn qisqartirildi - dastlabki {max_chars} ta belgi]:\n\n" + text[:max_chars]
        return text
    except Exception as e:
        return f"Hujjatni o'qishda xatolik yuz berdi: {e}"

def stop_youtube() -> str:
    """
    Stops YouTube playback by closing any open YouTube tabs in Google Chrome and Safari.
    Use this when the user wants to stop, turn off, pause, or close the YouTube music, song, or video.
    """
    print("🔧 Jarvis: YouTubedagi ijroni to'xtatmoqda (tablarni yopmoqda)...")
    try:
        # AppleScript for Google Chrome (safely loop end-to-beginning to avoid indexing bugs)
        chrome_script = """
        tell application "Google Chrome"
            set closed_any to false
            try
                repeat with w in windows
                    set tab_list to tabs of w
                    repeat with i from (count of tab_list) to 1 by -1
                        set t to item i of tab_list
                        if URL of t contains "youtube.com" or URL of t contains "youtu.be" then
                            close t
                            set closed_any to true
                        end if
                    end repeat
                end repeat
            end try
            return closed_any
        end tell
        """
        # AppleScript for Safari
        safari_script = """
        tell application "Safari"
            set closed_any to false
            try
                repeat with w in windows
                    set tab_list to tabs of w
                    repeat with i from (count of tab_list) to 1 by -1
                        set t to item i of tab_list
                        if URL of t contains "youtube.com" or URL of t contains "youtu.be" then
                            close t
                            set closed_any to true
                        end if
                    end repeat
                end repeat
            end try
            return closed_any
        end tell
        """
        
        chrome_res = subprocess.run(["osascript", "-e", chrome_script], capture_output=True, text=True).stdout.strip()
        safari_res = subprocess.run(["osascript", "-e", safari_script], capture_output=True, text=True).stdout.strip()
        
        if "true" in chrome_res or "true" in safari_res:
            return "YouTube ijrosi muvaffaqiyatli to'xtatildi."
        else:
            return "Hech qanday ochiq YouTube sahifasi topilmadi."
    except Exception as e:
        return f"YouTube ijrosini to'xtatishda xatolik: {e}"



