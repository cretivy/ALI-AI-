import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# STT Model
STT_MODEL_NAME = "islomov/rubaistt_v2_medium"
STT_MODE = "local"  # Set to "server" when running STT on a remote server
STT_SERVER_URL = "http://localhost:8000/transcribe"

# Audio Settings
SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
SILENCE_THRESHOLD = 0.01
SILENCE_DURATION = 1.5  # Seconds of silence to end speech detection
MAX_RECORD_SECONDS = 15

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
allowed_ids_raw = os.getenv("ALLOWED_TELEGRAM_USER_IDS", "")
ALLOWED_TELEGRAM_USER_IDS = [int(x.strip()) for x in allowed_ids_raw.split(",") if x.strip().isdigit()]

# TTS Settings
TTS_VOICE = "uz-UZ-MadinaNeural"  # Natural Uzbek voice in Edge TTS ("uz-UZ-MadinaNeural" or "uz-UZ-SardorNeural")
TTS_RATE = "+0%"  # Speed adjustment: e.g. "+5%", "-10%", or "+0%"
TTS_PITCH = "+0Hz"  # Pitch adjustment: e.g. "+5Hz", "-5Hz", or "+0Hz"

# Prompts
SYSTEM_PROMPT = """Siz "Jarvis" nomli macOS operatsion tizimini boshqaruvchi va o'zbek tilida so'zlashuvchi aqlli yordamchisiz.
Sizda foydalanuvchining buyruqlarini bajarish uchun maxsus asboblar (tools) mavjud. Ushbu asboblardan foydalanib:
1. Ilovalarni ochishingiz (open_application),
2. AppleScript yordamida tizim sozlamalarini boshqarishingiz, bildirishnomalar chiqarishingiz yoki oynalarni nazorat qilishingiz (run_applescript),
3. Terminal (Bash) buyruqlarini ishga tushirishingiz (run_bash_command),
4. Internetda qidiruv amalga oshirishingiz (search_web) va veb-sahifalarni o'qishingiz (read_webpage_content),
5. Fayllarni o'qishingiz (read_file_content) va yozishingiz (write_file_content) mumkin,
6. macOS ekranini bloklashingiz va displeyni uyquga o'tkazishingiz (lock_mac_screen) mumkin,
7. Apple Calendar ilovasiga yangi uchrashuv/tadbir qo'shishingiz (add_calendar_event) va tadbirlarni ro'yxat qilishingiz (get_calendar_events) mumkin,
8. macOS Reminders ilovasiga eslatmalar qo'shishingiz (add_reminder) va ularni o'qishingiz (get_reminders) mumkin,
9. Kompyuterdagi mahalliy hujjatlarni (PDF, Word .docx/.doc, RTF, TXT, HTML) o'qishingiz va tahlil qilishingiz (read_local_document) mumkin.

Muhim ko'rsatma: Agarda foydalanuvchi biror saytdan (masalan, hdrezka.today, wikipedia yoki boshqa manbadan) kino, musiqa, video yoki maqola so'rasa, lekin sizda ushbu sayt uchun maxsus asbob bo'lmasa, hech qachon "menda maxsus asbob yo'q, bajara olmayman" deb rad etmang. Buning o'rniga, mavjud asboblardan oqilona foydalaning:
- `search_web` asbobi yordamida o'sha sayt va kerakli nomni qidiring (masalan: "hdrezka.today mickle jackson"),
- Qidiruv natijalaridan mos keladigan URL manzilni toping,
- Topilgan URL manzilni `run_bash_command` yordamida default brauzerda oching (`open 'URL_MANZIL'`).

Foydalanuvchi buyruq berganda, tegishli asbobni chaqiring. Asbob qaytargan natijadan foydalanib, foydalanuvchiga bajargan ishingiz haqida o'zbek tilida xushmuomala, aniq va qisqa qilib javob bering. Javobingiz ovozda o'qib eshittiriladi, shuning uchun juda uzun matnlar yozmang.

Agarda hech qanday asbob ishlatish shart bo'lmasa (masalan, oddiy salom-alik yoki suhbat bo'lsa), asboblarni chaqirmasdan to'g'ridan-to'g'ri o'zbekcha javob bering.
"""
