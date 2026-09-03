import json
import re
import os
import config
from google.genai import types
from PIL import Image

from actions.tools import (
    open_application,
    run_applescript,
    run_bash_command,
    search_web,
    read_webpage_content,
    read_file_content,
    write_file_content,
    play_youtube,
    send_telegram_message,
    lock_mac_screen,
    add_calendar_event,
    get_calendar_events,
    add_reminder,
    get_reminders,
    read_local_document,
    stop_youtube,
    take_screenshot,
    take_webcam_photo,
    record_webcam_video_note,
    get_system_stats,
    set_system_volume,
    control_music,
    sleep_mac,
    search_and_send_file,
    set_timer,
    summarize_webpage
)

class JarvisBrain:
    def __init__(self, api_key=None):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                print("🧠 Gemini API bilan ulandi!")
            except Exception as e:
                print(f"⚠️ Gemini SDK ulanishida xatolik: {e}")

    def analyze_image(self, image_path: str, prompt: str = "") -> str:
        """Analyzes an image using Gemini Vision model and returns description/answer in Uzbek"""
        if not self.client:
            return "Kechirasiz, Gemini API ulanmaganligi sababli rasmni tahlil qila olmayman."
            
        try:
            print(f"👁️ Gemini Vision: Rasmni tahlil qilmoqda: {image_path}...")
            img = Image.open(image_path)
            full_prompt = prompt.strip() if prompt else "Ushbu rasmni o'zbek tilida batafsil va tushunarli qilib tahlil qilib ber."
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[img, full_prompt]
            )
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ Gemini Vision xatoligi: {e}")
            return f"Rasmni tahlil qilishda xatolik yuz berdi: {e}"

    def process_command(self, user_text):
        """Processes user Uzbek transcript and returns structured intent JSON"""
        if not user_text or not user_text.strip():
            return {
                "intent": "chat",
                "response_text": "Sizni eshitmadim, iltimos qaytadan gapiring.",
                "parameters": {}
            }

        # Try Gemini API if available
        if self.client:
            try:
                prompt = f"{config.SYSTEM_PROMPT}\n\nFoydalanuvchi buyrug'i: \"{user_text}\""
                tools_list = [
                    open_application,
                    run_applescript,
                    run_bash_command,
                    search_web,
                    read_webpage_content,
                    read_file_content,
                    write_file_content,
                    play_youtube,
                    send_telegram_message,
                    lock_mac_screen,
                    add_calendar_event,
                    get_calendar_events,
                    add_reminder,
                    get_reminders,
                    read_local_document,
                    stop_youtube,
                    take_screenshot,
                    take_webcam_photo,
                    record_webcam_video_note,
                    get_system_stats,
                    set_system_volume,
                    control_music,
                    sleep_mac,
                    search_and_send_file,
                    set_timer,
                    summarize_webpage
                ]
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=tools_list
                    )
                )
                raw_text = response.text.strip()
                
                # The tools were executed automatically under the hood.
                return {
                    "intent": "gemini_tool_execution",
                    "response_text": raw_text,
                    "parameters": {}
                }
            except Exception as e:
                print(f"⚠️ Gemini API xatoligi: {e}")
                error_str = str(e).lower()
                if "503" in error_str or "service unavailable" in error_str or "overloaded" in error_str:
                    return {
                        "intent": "error_503",
                        "response_text": "Kechirasiz, hozirda serverda vaqtincha yuqori yuklama bor. Iltimos, birozdan keyin qayta urinib ko'ring.",
                        "parameters": {}
                    }

        # Rule-based fallback intent engine
        return self._rule_based_fallback(user_text)

    def _rule_based_fallback(self, text):
        text_lower = text.lower()

        # Screenshot fallback
        if "ekran" in text_lower and ("rasm" in text_lower or "skrin" in text_lower or "ko'rsat" in text_lower or "yubor" in text_lower):
            res = take_screenshot()
            return {"intent": "screenshot", "response_text": f"Mac ekrani rasmga olindi.\n{res}", "parameters": {}}

        # Video note / Krujok fallback
        if "video" in text_lower or "krujok" in text_lower or "xonani ko'rsat" in text_lower:
            res = record_webcam_video_note(5)
            return {"intent": "video_note", "response_text": f"Xonadan video krujok yozib olindi.\n{res}", "parameters": {}}

        # Webcam photo fallback
        if "kamera" in text_lower or "foto" in text_lower:
            res = take_webcam_photo()
            return {"intent": "webcam_photo", "response_text": f"Kameradan foto surat olindi.\n{res}", "parameters": {}}

        # System stats fallback
        if any(w in text_lower for w in ["batareya", "xotira", "ram", "cpu", "disk", "tizim holati"]):
            res = get_system_stats()
            return {"intent": "system_stats", "response_text": res, "parameters": {}}

        # Shutdown intent
        if any(w in text_lower for w in ["o'chir", "yop", "chiqish", "xayr", "to'xta"]):
            return {
                "intent": "shutdown",
                "response_text": "Xayr! Jarvis faoliyati yakunlanmoqda.",
                "parameters": {}
            }

        # Telegram intent
        if "telegram" in text_lower:
            if "och" in text_lower:
                return {
                    "intent": "open_app",
                    "response_text": "Telegram ilovasini ochmoqdaman.",
                    "parameters": {"app_name": "Telegram"}
                }
            elif "yoz" in text_lower or "xabar" in text_lower:
                words = text_lower.split()
                recipient = "do'stim"
                if "ga" in text_lower:
                    match = re.search(r'(\w+)ga', text_lower)
                    if match:
                        recipient = match.group(1)
                return {
                    "intent": "telegram_send",
                    "response_text": f"Telegramdan {recipient}ga xabar yozish oynasini ochyapman.",
                    "parameters": {"recipient": recipient, "message": text}
                }

        # YouTube intent
        if "youtube" in text_lower or "qo'shiq" in text_lower or "musiqa" in text_lower or "vidio" in text_lower:
            query = text_lower.replace("youtube", "").replace("dan", "").replace("qo'shiq", "").replace("qoy", "").replace("qo'y", "").strip()
            if not query:
                query = "Uzbek music"
            return {
                "intent": "youtube_play",
                "response_text": f"Youtubedan {query} ijro etilmoqda.",
                "parameters": {"query": query}
            }

        # Open App intent
        if "och" in text_lower or "yoq" in text_lower:
            apps = ["safari", "chrome", "spotify", "finder", "notes", "calculator"]
            for app in apps:
                if app in text_lower:
                    return {
                        "intent": "open_app",
                        "response_text": f"{app.capitalize()} ilovasi ochilmoqda.",
                        "parameters": {"app_name": app}
                    }

        # Default Chat
        return {
            "intent": "chat",
            "response_text": f"Tushundim: \"{text}\". Yana qanday yordam bera olaman?",
            "parameters": {}
        }

if __name__ == "__main__":
    brain = JarvisBrain()
    res = brain.process_command("Mac batareyasi qancha qolgan?")
    print(res)
