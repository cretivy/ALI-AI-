import os
import sys
import time
import tempfile
import subprocess
import requests
import re
import soundfile as sf
import numpy as np

# Ensure project path is loaded
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from brain import JarvisBrain
from tts import UzbekTTS
from stt import UzbekSTT

class JarvisTelegramBot:
    def __init__(self, brain=None, stt=None, tts=None):
        self.token = config.TELEGRAM_BOT_TOKEN
        if not self.token:
            print("❌ Xatolik: .env faylida TELEGRAM_BOT_TOKEN topilmadi!")
            sys.exit(1)
            
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.file_url = f"https://api.telegram.org/file/bot{self.token}"
        
        self.brain = brain or JarvisBrain()
        self.stt = stt or UzbekSTT()
        self.tts = tts or UzbekTTS()
        
        print("🤖 Jarvis Telegram Boti ishga tushdi!")
        if not config.ALLOWED_TELEGRAM_USER_IDS:
            print("⚠️ DIQQAT: Ruxsat berilgan foydalanuvchilar ro'yxati bo'sh.")
            print("🔒 Botga birinchi bo'lib yozgan foydalanuvchi avtomatik ravishda uning egasi (Owner) etib tayinlanadi!")
            
    def write_owner_id_to_env(self, user_id):
        """Saves the first user's ID to .env file as owner"""
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        try:
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                new_lines = []
                found = False
                for line in lines:
                    if line.startswith("ALLOWED_TELEGRAM_USER_IDS="):
                        new_lines.append(f"ALLOWED_TELEGRAM_USER_IDS={user_id}\n")
                        found = True
                    else:
                        new_lines.append(line)
                
                if not found:
                    new_lines.append(f"ALLOWED_TELEGRAM_USER_IDS={user_id}\n")
                    
                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                    
                # Dynamically update in running config
                config.ALLOWED_TELEGRAM_USER_IDS = [user_id]
                print(f"🔒 Foydalanuvchi ID {user_id} tizim egasi etib tayinlandi va .env fayliga yozildi.")
            else:
                print("⚠️ .env fayli topilmadi, ID saqlanmadi.")
        except Exception as e:
            print(f"⚠️ .env fayliga yozishda xatolik: {e}")

    def is_authorized(self, user_id):
        """Checks if the user is authorized to issue commands to Jarvis"""
        if not config.ALLOWED_TELEGRAM_USER_IDS:
            # Auto-authorize first user
            self.write_owner_id_to_env(user_id)
            return True
            
        return user_id in config.ALLOWED_TELEGRAM_USER_IDS

    def convert_ogg_to_wav(self, ogg_path, wav_path):
        """Converts Telegram .ogg (Opus) to standard 16kHz WAV mono"""
        try:
            ffmpeg_path = "ffmpeg"
            if os.path.exists("/opt/homebrew/bin/ffmpeg"):
                ffmpeg_path = "/opt/homebrew/bin/ffmpeg"
                
            cmd = [ffmpeg_path, "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                return True
            else:
                print(f"⚠️ Ffmpeg error: {proc.stderr}")
                return False
        except Exception as e:
            print(f"⚠️ Ffmpeg execution error: {e}")
            return False

    def send_photo(self, chat_id, photo_path, caption=""):
        """Sends photo to Telegram chat"""
        try:
            with open(photo_path, "rb") as f:
                r = requests.post(
                    f"{self.api_url}/sendPhoto",
                    data={"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"},
                    files={"photo": f},
                    timeout=30
                )
                print(f"📸 Telegram SendPhoto natijasi: {r.status_code}")
        except Exception as e:
            print(f"⚠️ Photo sending error: {e}")

    def send_video_note(self, chat_id, video_path):
        """Sends 1:1 round video note ('krujok') to Telegram chat"""
        try:
            print(f"📤 Telegram'ga video note ('krujok') yuborilmoqda... Path: {video_path}")
            with open(video_path, "rb") as f:
                r = requests.post(
                    f"{self.api_url}/sendVideoNote",
                    data={"chat_id": chat_id},
                    files={"video_note": f},
                    timeout=45
                )
                print(f"📹 Telegram SendVideoNote natijasi: {r.status_code} - {r.text[:200]}")
        except Exception as e:
            print(f"⚠️ Video note sending error: {e}")

    def send_document(self, chat_id, doc_path, caption=""):
        """Sends local document/file to Telegram chat"""
        try:
            with open(doc_path, "rb") as f:
                r = requests.post(
                    f"{self.api_url}/sendDocument",
                    data={"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"},
                    files={"document": f},
                    timeout=60
                )
                print(f"📁 Telegram SendDocument natijasi: {r.status_code}")
        except Exception as e:
            print(f"⚠️ Document sending error: {e}")


    def process_and_send_response(self, chat_id, response_text):
        """Checks response text for media paths and drains pending media queue to send files to Telegram and clean up"""
        clean_text = response_text
        sent_paths = set()
        
        # 1. Check text tags (SCREENSHOT_PATH, WEBCAM_PATH, VIDEO_NOTE_PATH, FILE_PATH)
        if "SCREENSHOT_PATH:" in clean_text:
            match = re.search(r'SCREENSHOT_PATH:(\S+)', clean_text)
            if match:
                path = match.group(1).strip()
                clean_text = clean_text.replace(f"SCREENSHOT_PATH:{path}", "").strip()
                if os.path.exists(path) and path not in sent_paths:
                    self.send_photo(chat_id, path, caption="📸 Mac Ekran Skrinshoti")
                    sent_paths.add(path)
                    try:
                        os.remove(path)
                        print(f"🧹 Avtomatik tozalandi: {path}")
                    except Exception:
                        pass
                        
        if "WEBCAM_PATH:" in clean_text:
            match = re.search(r'WEBCAM_PATH:(\S+)', clean_text)
            if match:
                path = match.group(1).strip()
                clean_text = clean_text.replace(f"WEBCAM_PATH:{path}", "").strip()
                if os.path.exists(path) and path not in sent_paths:
                    self.send_photo(chat_id, path, caption="📷 Mac Kamerasidan Foto")
                    sent_paths.add(path)
                    try:
                        os.remove(path)
                        print(f"🧹 Avtomatik tozalandi: {path}")
                    except Exception:
                        pass

        if "VIDEO_NOTE_PATH:" in clean_text:
            match = re.search(r'VIDEO_NOTE_PATH:(\S+)', clean_text)
            if match:
                path = match.group(1).strip()
                clean_text = clean_text.replace(f"VIDEO_NOTE_PATH:{path}", "").strip()
                if os.path.exists(path) and path not in sent_paths:
                    self.send_video_note(chat_id, path)
                    sent_paths.add(path)
                    try:
                        os.remove(path)
                        print(f"🧹 Avtomatik tozalandi: {path}")
                    except Exception:
                        pass

        if "FILE_PATH:" in clean_text:
            match = re.search(r'FILE_PATH:(\S+)', clean_text)
            if match:
                path = match.group(1).strip()
                clean_text = clean_text.replace(f"FILE_PATH:{path}", "").strip()
                if os.path.exists(path) and path not in sent_paths:
                    self.send_document(chat_id, path, caption=f"📁 Fayl: {os.path.basename(path)}")
                    sent_paths.add(path)
                    if path.startswith("/tmp/"):
                        try:
                            os.remove(path)
                            print(f"🧹 Avtomatik tozalandi: {path}")
                        except Exception:
                            pass

        # 2. Drain registered pending media files queue
        try:
            from actions.tools import get_and_clear_pending_media
            pending_items = get_and_clear_pending_media()
            for item in pending_items:
                m_type = item.get("type")
                path = item.get("path")
                if path and os.path.exists(path) and path not in sent_paths:
                    sent_paths.add(path)
                    if m_type == "video_note":
                        self.send_video_note(chat_id, path)
                    elif m_type in ["screenshot", "webcam_photo"]:
                        caption = "📸 Mac Ekran Skrinshoti" if m_type == "screenshot" else "📷 Mac Kamerasidan Foto"
                        self.send_photo(chat_id, path, caption=caption)
                    elif m_type == "file":
                        self.send_document(chat_id, path, caption=f"📁 Fayl: {os.path.basename(path)}")

                    # Cleanup file from /tmp/
                    if path.startswith("/tmp/"):
                        try:
                            os.remove(path)
                            print(f"🧹 Avtomatik tozalandi: {path}")
                        except Exception as e:
                            print(f"⚠️ Faylni o'chirishda xatolik: {e}")
        except Exception as e:
            print(f"⚠️ Pending media delivery error: {e}")

        if not clean_text or clean_text.strip() == "":
            clean_text = "Buyruq bajarildi."
            
        return clean_text


    def handle_voice_message(self, file_id, chat_id):
        """Downloads, transcribes voice message, runs intent, and replies with voice + text"""
        print(f"🎙️ Yangi ovozli xabar qabul qilindi. File ID: {file_id}")
        
        try:
            # 1. Get file path from Telegram API
            r = requests.get(f"{self.api_url}/getFile", params={"file_id": file_id}, timeout=10)
            if r.status_code != 200:
                print(f"⚠️ getFile failed: {r.text}")
                return
                
            file_path = r.json().get("result", {}).get("file_path")
            if not file_path:
                print("⚠️ File path not found in Telegram response.")
                return
                
            # 2. Download OGG file
            ogg_url = f"{self.file_url}/{file_path}"
            ogg_data = requests.get(ogg_url, timeout=20).content
            
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_ogg:
                temp_ogg.write(ogg_data)
                ogg_path = temp_ogg.name
                
            # 3. Convert OGG to WAV
            wav_path = ogg_path.replace(".ogg", ".wav")
            conversion_success = self.convert_ogg_to_wav(ogg_path, wav_path)
            
            # Clean up temp OGG
            if os.path.exists(ogg_path):
                os.remove(ogg_path)
                
            if not conversion_success:
                self.send_message(chat_id, "⚠️ Ovozli faylni qayta ishlashda xatolik yuz berdi (ffmpeg).")
                return
                
            # 4. Transcribe using STT
            audio_data, sample_rate = sf.read(wav_path)
            # Clean up temp WAV
            if os.path.exists(wav_path):
                os.remove(wav_path)
                
            transcript = self.stt.transcribe(audio_data, sample_rate=sample_rate)
            if not transcript or len(transcript.strip()) < 2:
                self.send_message(chat_id, "💬 Ovozni eshitib bo'lmadi. Iltimos, aniqroq gapiring.")
                return
                
            print(f"📝 Olingan ovozli matn: \"{transcript}\"")
            self.send_message(chat_id, f"📝 *Olingan Ovoz:* \"{transcript}\"")
            
            # 5. Process command using Gemini Brain
            intent_data = self.brain.process_command(transcript)
            raw_response_text = intent_data.get("response_text", "Amal bajarildi.")
            
            # 6. Send any attached media (photos, video notes, docs) & clean text
            clean_text = self.process_and_send_response(chat_id, raw_response_text)
            
            # 7. Send response as voice and text
            self.send_voice_response(chat_id, clean_text)
            
        except Exception as e:
            print(f"⚠️ Ovozli xabarni qayta ishlashda xatolik: {e}")
            self.send_message(chat_id, f"⚠️ Xatolik yuz berdi: {e}")

    def handle_text_message(self, text, chat_id):
        """Processes text command via brain, executes, and replies with voice + text"""
        print(f"💬 Yangi matnli xabar: \"{text}\"")
        
        try:
            # Process command
            intent_data = self.brain.process_command(text)
            raw_response_text = intent_data.get("response_text", "Amal bajarildi.")
            
            # Send media if any & clean text
            clean_text = self.process_and_send_response(chat_id, raw_response_text)
            
            # Reply
            self.send_voice_response(chat_id, clean_text)
        except Exception as e:
            print(f"⚠️ Matnli xabarni qayta ishlashda xatolik: {e}")
            self.send_message(chat_id, f"⚠️ Xatolik yuz berdi: {e}")

    def handle_photo_message(self, photo_array, chat_id, caption=""):
        """Downloads photo, sends to Gemini Vision, and replies with analysis"""
        print(f"🖼️ Yangi rasm qabul qilindi. Chat ID: {chat_id}")
        try:
            photo = photo_array[-1]
            file_id = photo["file_id"]
            
            r = requests.get(f"{self.api_url}/getFile", params={"file_id": file_id}, timeout=10)
            if r.status_code != 200:
                self.send_message(chat_id, "⚠️ Rasmni Telegramdan yuklab bo'lmadi.")
                return
                
            file_path = r.json().get("result", {}).get("file_path")
            img_url = f"{self.file_url}/{file_path}"
            img_bytes = requests.get(img_url, timeout=20).content
            
            temp_img_path = "/tmp/telegram_incoming_img.jpg"
            with open(temp_img_path, "wb") as f:
                f.write(img_bytes)
                
            analysis = self.brain.analyze_image(temp_img_path, prompt=caption)
            
            # Clean up temp image immediately
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
                print(f"🧹 Avtomatik tozalandi: {temp_img_path}")
                
            self.send_voice_response(chat_id, analysis)
        except Exception as e:
            print(f"⚠️ Rasm tahlilida xatolik: {e}")
            self.send_message(chat_id, f"⚠️ Rasmni tahlil qilishda xatolik yuz berdi: {e}")

    def send_message(self, chat_id, text):
        """Sends text message to Telegram chat"""
        try:
            requests.post(
                f"{self.api_url}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=10
            )
        except Exception as e:
            print(f"⚠️ Message sending error: {e}")

    def send_voice_response(self, chat_id, text):
        """Synthesizes text and sends it as a Telegram Voice Note"""
        # Send text confirmation first
        self.send_message(chat_id, f"🗣️ *Jarvis:* {text}")
        
        # Generate Voice file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
            temp_voice_path = fp.name
            
        try:
            import asyncio
            asyncio.run(self.tts._generate_audio(text, temp_voice_path))
            
            with open(temp_voice_path, "rb") as voice_file:
                requests.post(
                    f"{self.api_url}/sendVoice",
                    data={"chat_id": chat_id},
                    files={"voice": voice_file},
                    timeout=15
                )
        except Exception as e:
            print(f"⚠️ Voice sending error: {e}")
        finally:
            if os.path.exists(temp_voice_path):
                os.remove(temp_voice_path)

    def start_polling(self):
        """Starts long polling loop for updates from Telegram"""
        print("\n🤖 Telegram Polling boshlandi. Botga Telegram ilovasida xabar yozishingiz mumkin...")
        print("💡 Eslatma: Dastur ishlashini to'xtatish uchun Ctrl+C tugmalarini bosing.")
        
        offset = 0
        while True:
            try:
                r = requests.get(
                    f"{self.api_url}/getUpdates",
                    params={"offset": offset, "timeout": 30},
                    timeout=35
                )
                if r.status_code != 200:
                    time.sleep(2)
                    continue
                    
                updates = r.json().get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    
                    message = update.get("message")
                    if not message:
                        continue
                        
                    chat_id = message["chat"]["id"]
                    user_id = message["from"]["id"]
                    first_name = message["from"].get("first_name", "Foydalanuvchi")
                    
                    # Security Whitelist check
                    if not self.is_authorized(user_id):
                        print(f"🔒 Ruxsat etilmagan foydalanuvchi urinishi! ID: {user_id}, Name: {first_name}")
                        self.send_message(
                            chat_id, 
                            "🔒 *Ruxsat berilmagan!* \nSiz ushbu Jarvis boshqaruv boti egasi emassiz."
                        )
                        continue
                        
                    # Handle Voice message
                    if "voice" in message:
                        file_id = message["voice"]["file_id"]
                        self.handle_voice_message(file_id, chat_id)
                        
                    # Handle Audio message (in case it is uploaded as file)
                    elif "audio" in message:
                        file_id = message["audio"]["file_id"]
                        self.handle_voice_message(file_id, chat_id)

                    # Handle Photo message
                    elif "photo" in message:
                        caption = message.get("caption", "")
                        self.handle_photo_message(message["photo"], chat_id, caption)
                        
                    # Handle Text message
                    elif "text" in message:
                        text = message["text"].strip()
                        if text == "/start":
                            self.send_message(
                                chat_id,
                                f"🤖 *Assalomu alaykum, {first_name}!* \n"
                                "Men sizning Mac kompyuteringizni masofadan boshqaruvchi Jarvis botiman.\n\n"
                                "Siz menga ovozli xabar yuborishingiz, rasm jo'natishingiz yoki matnli buyruq kiritishingiz mumkin.\n\n"
                                "📸 _'Ekranni rasmga olib yubor'_\n"
                                "⭕ _'Xonani videoga olib yubor (krujok)'_\n"
                                "📊 _'Batareya va xotira holati qanday?'_\n"
                                "🎵 _'Musiqani to'xtat'_\n"
                                "⏰ _'10 daqiqadan keyin taymer ber'_\n"
                                "🖼️ _Rasm yuborsangiz, uni AI orqali tahlil qilib beraman!_"
                            )
                        else:
                            self.handle_text_message(text, chat_id)
                            
            except KeyboardInterrupt:
                print("\n🤖 Telegram Bot polling to'xtatildi.")
                break
            except Exception as e:
                print(f"⚠️ Polling xatoligi: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bot = JarvisTelegramBot()
    bot.start_polling()
