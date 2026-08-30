import asyncio
import os
import subprocess
import tempfile
import edge_tts
import config

class UzbekTTS:
    def __init__(self, voice=config.TTS_VOICE, rate=config.TTS_RATE, pitch=config.TTS_PITCH):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch

    async def _generate_audio(self, text, output_file):
        communicate = edge_tts.Communicate(
            text, 
            self.voice, 
            rate=self.rate, 
            pitch=self.pitch
        )
        await communicate.save(output_file)

    def speak(self, text):
        """Synthesize Uzbek text and play it out loud via macOS afplay"""
        if not text or not text.strip():
            return

        print(f"🗣️ Jarvis: {text}")

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
            temp_path = fp.name

        try:
            asyncio.run(self._generate_audio(text, temp_path))
            # Use native macOS audio player afplay
            subprocess.run(["afplay", temp_path], check=False)
        except Exception as e:
            print(f"⚠️ TTS Xatosi: {e}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    tts = UzbekTTS()
    tts.speak("Assalomu alaykum! Men Jarvisman, sizga qanday yordam bera olaman?")
