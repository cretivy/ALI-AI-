import sys
import os
import time
import threading
import rumps

from license import check_saved_license, verify_license
from stt import UzbekSTT
from tts import UzbekTTS
from brain import JarvisBrain
from actions.tools import toggle_gesture_control

class MunisaMacApp(rumps.App):
    def __init__(self):
        super(MunisaMacApp, self).__init__("🤖 Munisa AI", icon=None, quit_button=None)
        
        # Verify License Key
        self.license_valid, self.license_msg = check_saved_license()
        
        # Initialize Core Modules
        self.stt = UzbekSTT()
        self.tts = UzbekTTS()
        self.brain = JarvisBrain()
        self.is_recording = False
        self.gesture_enabled = False

        # Menu Items
        self.listen_item = rumps.MenuItem("🎤 Ovozli Buyruq Berish", callback=self.on_listen_click)
        self.gesture_item = rumps.MenuItem("✋ Qo'l Harakati Boshqaruvi: OFF", callback=self.on_gesture_toggle)
        self.license_item = rumps.MenuItem(f"🔑 Litsenziya: {'FAOL ✅' if self.license_valid else 'XATO ❌'}", callback=self.on_license_click)
        self.quit_item = rumps.MenuItem("❌ Chiqish", callback=self.on_quit)

        self.menu = [
            self.listen_item,
            self.gesture_item,
            None,  # Separator
            self.license_item,
            None,  # Separator
            self.quit_item
        ]

        # Welcome notification
        if self.license_valid:
            rumps.notification("Munisa AI", "Tizim tayyor!", "Assalomu alaykum jonim! Men Munisaman.")
        else:
            rumps.notification("Munisa AI Warning", "Litsenziya yo'q", "Iltimos, litsenziya kalitini kiriting!")

    @rumps.clicked("🎤 Ovozli Buyruq Berish")
    def on_listen_click(self, sender):
        if not self.license_valid:
            rumps.alert("Litsenziya Xatosi", "Iltimos, avval litsenziya kalitini kiriting!")
            return

        if self.is_recording:
            return
        
        self.is_recording = True
        self.title = "🔴 Eshitmoqda..."
        
        # Run audio recording in background thread
        threading.Thread(target=self._process_voice_command, daemon=True).start()

    def _process_voice_command(self):
        try:
            # Play prompt sound/greeting
            self.tts.speak("Eshitaman hayotim!")
            
            # Record 5 seconds of audio
            audio_path = self.stt.record_audio(duration=5)
            self.title = "🧠 Tahlil qilinmoqda..."
            
            # Transcribe
            text = self.stt.transcribe(audio_path)
            if not text:
                self.title = "🤖 Munisa AI"
                self.tts.speak("Sizni eshitmadim hayotim.")
                self.is_recording = False
                return

            rumps.notification("Munisa AI", "Buyruq olindi:", text)
            
            # Gemini Brain Intent Execution
            result = self.brain.process_command(text)
            response_text = result.get("response_text", "Bajarildi!")
            
            # Speak response
            self.tts.speak(response_text)
            
        except Exception as e:
            print(f"⚠️ App Voice Error: {e}")
            rumps.notification("Munisa AI Error", "Xatolik", str(e))
        finally:
            self.title = "🤖 Munisa AI"
            self.is_recording = False

    @rumps.clicked("✋ Qo'l Harakati Boshqaruvi: OFF")
    def on_gesture_toggle(self, sender):
        self.gesture_enabled = not self.gesture_enabled
        res = toggle_gesture_control(self.gesture_enabled)
        
        if self.gesture_enabled:
            sender.title = "✋ Qo'l Harakati Boshqaruvi: ON ✅"
            rumps.notification("Munisa AI", "Gesture Mode ON", "Kamerangizga qo'lingiz bilan swipe qiling!")
        else:
            sender.title = "✋ Qo'l Harakati Boshqaruvi: OFF"
            rumps.notification("Munisa AI", "Gesture Mode OFF", "Qo'l harakatlari o'chirildi.")

    @rumps.clicked("🔑 Litsenziya")
    def on_license_click(self, sender):
        valid, msg = check_saved_license()
        if valid:
            rumps.alert("Litsenziya Holati", f"✅ {msg}")
        else:
            response = rumps.Window(
                message="Litsenziya kalitingizni kiriting (Masalan: MUNISA-PRO-9999-2026):",
                title="Munisa AI Activation",
                default_text="",
                ok="Faollashtirish",
                cancel="Bekor qilish"
            ).run()
            
            if response.clicked:
                key = response.text.strip()
                v, m = verify_license(key)
                if v:
                    self.license_valid = True
                    self.license_item.title = "🔑 Litsenziya: FAOL ✅"
                    rumps.alert("Muvaffaqiyatli!", f"✅ {m}")
                else:
                    rumps.alert("Xatolik!", f"❌ {m}")

    def on_quit(self, sender):
        rumps.quit_application()

if __name__ == "__main__":
    app = MunisaMacApp()
    app.run()
