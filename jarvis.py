import sys
import os
import time
import threading
import config
from stt import UzbekSTT
from tts import UzbekTTS
from brain import JarvisBrain
from ui import show_banner, show_status, show_transcript, show_action_result
from actions.mac_actions import open_app, set_volume, notify_mac
from actions.telegram import handle_telegram_action
from actions.youtube import play_youtube

# Import Web UI Controller
try:
    from web_ui import gui
    HAS_WEB_UI = True
except Exception as e:
    HAS_WEB_UI = False
    print(f"Web UI yuklanmadi: {e}")

class JarvisAssistant:
    def __init__(self):
        show_banner()
        show_status("Tizim ishga tushirilmoqda...", "bold yellow")
        
        # Initialize modules
        self.stt = UzbekSTT()
        self.tts = UzbekTTS()
        self.brain = JarvisBrain()

        # Connect UI JsAPI to this assistant instance
        if HAS_WEB_UI and gui:
            gui.api.set_assistant(self)

        # Start Telegram Bot automatically in a background daemon thread
        try:
            from telegram_bot import JarvisTelegramBot
            self.tg_bot = JarvisTelegramBot(brain=self.brain, stt=self.stt, tts=self.tts)
            self.tg_thread = threading.Thread(target=self.tg_bot.start_polling, daemon=True)
            self.tg_thread.start()
            show_status("Telegram masofaviy boshqaruv boti fonda faollashtirildi.", "bold green")
        except Exception as e:
            show_status(f"Telegram botni faollashtirishda xatolik: {e}", "bold red")

        # Welcome greeting
        welcome_msg = "Assalomu alaykum jonim! Men Munisaman, xizmatingizdaman, hayotim."
        show_status(welcome_msg, "bold green")
        
        if HAS_WEB_UI and gui:
            gui.set_state("idle", "", welcome_msg)
            
        self.tts.speak("Assalomu alaykum jonim! Men Munisaman, xizmatingizdaman, hayotim.")

    def execute_action(self, intent_data, user_text=""):
        intent = intent_data.get("intent", "chat")
        raw_response_text = intent_data.get("response_text", "Buyruq bajarildi.")
        params = intent_data.get("parameters", {})
        action_detail = ""

        # Deliver media to Telegram if available and authorized user exists
        clean_text = raw_response_text
        if hasattr(self, "tg_bot") and self.tg_bot and config.ALLOWED_TELEGRAM_USER_IDS:
            owner_id = config.ALLOWED_TELEGRAM_USER_IDS[0]
            clean_text = self.tg_bot.process_and_send_response(owner_id, raw_response_text)

        # Update HUD state to SPEAKING
        if HAS_WEB_UI and gui:
            gui.set_state("speaking", user_text, clean_text)

        # Speak clean voice response to user
        self.tts.speak(clean_text)

        # Dispatch action based on intent
        if intent == "gemini_tool_execution":
            action_detail = "Gemini asboblari orqali avtomatik bajarildi."
        elif intent == "open_app":
            app_name = params.get("app_name", "Telegram")
            success, action_detail = open_app(app_name)
        elif intent == "telegram_send":
            recipient = params.get("recipient")
            message = params.get("message")
            success, action_detail = handle_telegram_action(recipient, message)
        elif intent == "youtube_play":
            query = params.get("query", "Uzbek music")
            success, action_detail = play_youtube(query)
        elif intent == "system_control":
            action = params.get("action", "volume_up")
            success, action_detail = set_volume(action)
        elif intent == "shutdown":
            action_detail = "Jarvis to'liq o'chirildi."
            show_action_result(intent, clean_text, action_detail)
            if HAS_WEB_UI and gui:
                gui.set_state("idle", "", "O'chirildi.")
            sys.exit(0)
        else:
            action_detail = "Suhbat rejasi bajarildi."

        show_action_result(intent, clean_text, action_detail)

        # Reset HUD to IDLE
        if HAS_WEB_UI and gui:
            gui.set_state("idle", user_text, clean_text)

    def listen_and_process(self, record_duration=6):
        """One round of listening, transcription, thinking, and executing action"""
        show_status("Mikrofon aktivlashtirildi. 6 sekund gapiring...", "bold cyan")
        
        # Update HUD state to LISTENING
        if HAS_WEB_UI and gui:
            gui.set_state("listening", "Ovoz tinglanmoqda...", "")
            
        # Capture audio while feeding real-time audio levels to GUI
        audio_callback = gui.set_audio_level if (HAS_WEB_UI and gui) else None
        audio_data = self.stt.record_audio_vad(duration=record_duration, audio_callback=audio_callback)

        if audio_data is None or len(audio_data) == 0:
            show_status("Hech qanday ovoz yozilmadi.", "bold red")
            if HAS_WEB_UI and gui:
                gui.set_state("idle", "Ovoz yozilmadi", "")
            return

        # Update HUD state to THINKING
        if HAS_WEB_UI and gui:
            gui.set_state("thinking", "Tahlil qilinmoqda...", "")

        show_status("Ovoz o'zbek tilida tahlil qilinmoqda (rubaistt_v2_medium)...", "bold magenta")
        transcript = self.stt.transcribe(audio_data)

        if not transcript or len(transcript.strip()) < 2:
            show_status("Ovozni tanib bo'lmadi. Qayta urinib ko'ring.", "bold red")
            if HAS_WEB_UI and gui:
                gui.set_state("speaking", "Ovoz tanilmadi", "Sizni yaxshi eshitolmadim")
            self.tts.speak("Sizni yaxshi eshitolmadim, iltimos qaytadan gapiring.")
            if HAS_WEB_UI and gui:
                gui.set_state("idle", "", "")
            return

        show_transcript(transcript)
        if HAS_WEB_UI and gui:
            gui.set_state("thinking", transcript, "Jarvis o'ylamoqda...")

        show_status("Gemini API orqali buyruq ma'nosi aniqlanmoqda...", "bold yellow")
        intent_data = self.brain.process_command(transcript)

        self.execute_action(intent_data, user_text=transcript)

    def run_interactive_loop(self):
        """Continuous CLI menu loop"""
        print("\n" + "="*50)
        print("💡 BUYRUQ REJIMLARI:")
        print(" [1] Ovozli buyruq berish (Mikrofonga gapirish)")
        print(" [2] Matnli buyruq kiritish (Test uchun)")
        print(" [3] Chaqirish rejimi (Har gal Enter bosish)")
        print(" [q] Chiqish (Quit)")
        print("="*50)

        while True:
            try:
                choice = input("\n👉 Tanlov [1/2/3/q]: ").strip().lower()
                if choice == "1" or choice == "":
                    self.listen_and_process(record_duration=6)
                elif choice == "2":
                    user_text = input("💬 O'zbekcha buyruqni kiriting: ").strip()
                    if user_text:
                        show_transcript(user_text)
                        if HAS_WEB_UI and gui:
                            gui.set_state("thinking", user_text, "Jarvis o'ylamoqda...")
                        intent_data = self.brain.process_command(user_text)
                        self.execute_action(intent_data, user_text=user_text)
                elif choice == "3":
                    input("\n🎤 Tayyor bo'lsangiz ENTER tugmasini bosing...")
                    self.listen_and_process(record_duration=6)
                elif choice in ["q", "exit", "chiqish"]:
                    show_status("Jarvis faoliyati yakunlandi. Xayr!", "bold green")
                    if HAS_WEB_UI and gui:
                        gui.set_state("idle", "", "Salomat bo'ling!")
                    self.tts.speak("Xayr, salomat bo'ling!")
                    break
            except KeyboardInterrupt:
                print("\nJarvis to'xtatildi.")
                break

def main():
    use_cli = "--cli" in sys.argv or not HAS_WEB_UI

    assistant = JarvisAssistant()

    if not use_cli and HAS_WEB_UI and gui:
        print("🖥️ JARVIS Stark HUD interfeysi ochilmoqda...")
        # Start PyWebView GUI on the main thread safely
        gui.start_window()
    else:
        assistant.run_interactive_loop()

if __name__ == "__main__":
    main()
