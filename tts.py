import asyncio
import os
import subprocess
import tempfile
import requests
import edge_tts
import config

def add_uzbek_word_stress(word: str) -> str:
    """Applies Uzbek grammatical stress mark on the last vowel of multi-syllable words for natural AI pronunciation"""
    vowels = set("аеёиоуўэюяАЕЁИОУЎЭЮЯ")
    if '\u0301' in word or len(word) <= 2:
        return word

    indices = [i for i, c in enumerate(word) if c in vowels]
    if len(indices) > 1:
        last_v_idx = indices[-1]
        if last_v_idx + 1 < len(word) and word[last_v_idx+1] == '\u0301':
            return word
        return word[:last_v_idx+1] + '\u0301' + word[last_v_idx+1:]
    return word

def latin_to_cyrillic(text: str) -> str:
    """Converts Uzbek Latin text to Cyrillic phonetics with native Uzbek word stress for perfect ElevenLabs pronunciation"""
    # Specific word overrides with vocal stress mark on single vowel
    overrides = [
        ("hayotim", "хаёти́м"),
        ("Hayotim", "Хаёти́м"),
        ("jonim", "жони́м"),
        ("Jonim", "Жони́м"),
        ("adasi", "адаси́"),
        ("Adasi", "Адаси́"),
        ("adajonisi", "адажониси́"),
        ("Adajonisi", "Адажониси́"),
        ("xo'p", "хў́п"),
        ("Xo'p", "Хў́п"),
    ]
    res = text
    for word, cyr in overrides:
        res = res.replace(word, cyr)

    # Uzbek specific phonetic rules
    mapping = [
        ("sh", "ш"), ("Sh", "Ш"), ("SH", "Ш"),
        ("ch", "ч"), ("Ch", "Ч"), ("CH", "Ч"),
        ("yo'", "ё"), ("yo", "ё"), ("Yo'", "Ё"), ("Yo", "Ё"),
        ("yu", "ю"), ("Yu", "Ю"),
        ("ya", "я"), ("Ya", "Я"),
        ("o'", "ў"), ("O'", "Ў"), ("o`", "ў"), ("O`", "Ў"), ("oʼ", "ў"),
        ("g'", "ғ"), ("G'", "Ғ"), ("g`", "ғ"), ("G`", "Ғ"), ("gʼ", "ғ"),
        ("a", "а"), ("A", "А"),
        ("b", "б"), ("B", "Б"),
        ("d", "д"), ("D", "Д"),
        ("e", "е"), ("E", "Е"),
        ("f", "ф"), ("F", "Ф"),
        ("g", "г"), ("G", "Г"),
        ("h", "ҳ"), ("H", "Ҳ"),
        ("i", "и"), ("I", "И"),
        ("j", "ж"), ("J", "Ж"),
        ("k", "к"), ("K", "К"),
        ("l", "л"), ("L", "Л"),
        ("m", "м"), ("M", "М"),
        ("n", "н"), ("N", "Н"),
        ("o", "о"), ("O", "О"),
        ("p", "п"), ("P", "П"),
        ("q", "қ"), ("Q", "Қ"),
        ("r", "р"), ("R", "Р"),
        ("s", "с"), ("S", "С"),
        ("t", "т"), ("T", "Т"),
        ("u", "у"), ("U", "У"),
        ("v", "в"), ("V", "В"),
        ("x", "х"), ("X", "Х"),
        ("y", "й"), ("Y", "Й"),
        ("z", "з"), ("Z", "З")
    ]
    for lat, cyr in mapping:
        res = res.replace(lat, cyr)

    # Automatically add native Uzbek stress mark on the last vowel of each word
    words = res.split(" ")
    stressed_words = [add_uzbek_word_stress(w) for w in words]
    return " ".join(stressed_words)

class UzbekTTS:
    def __init__(self, voice=config.TTS_VOICE, rate=config.TTS_RATE, pitch=config.TTS_PITCH):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.eleven_api_key = config.ELEVENLABS_API_KEY
        self.eleven_voice_id = config.ELEVENLABS_VOICE_ID
        self.eleven_model_id = config.ELEVENLABS_MODEL_ID

    def _generate_elevenlabs_audio(self, text, output_file):
        """Generates Ultra-HD voice audio using ElevenLabs Multilingual V2 with accent optimization"""
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.eleven_voice_id}"
        headers = {
            "xi-api-key": self.eleven_api_key,
            "Content-Type": "application/json"
        }
        
        # Convert Latin text to Cyrillic phonetics to eliminate American/English accent
        phonetic_text = latin_to_cyrillic(text)
        
        data = {
            "text": phonetic_text,
            "model_id": self.eleven_model_id,
            "voice_settings": {
                "stability": 0.40,
                "similarity_boost": 0.92,
                "style": 0.12,
                "use_speaker_boost": True,
                "speed": 1.0
            }
        }
        r = requests.post(url, json=data, headers=headers, timeout=20)
        if r.status_code == 200 and len(r.content) > 100:
            with open(output_file, "wb") as f:
                f.write(r.content)
            return True
        else:
            print(f"⚠️ ElevenLabs API Xatosi ({r.status_code}): {r.text[:200]}")
            return False

    async def _generate_edge_audio(self, text, output_file):
        communicate = edge_tts.Communicate(
            text, 
            self.voice, 
            rate=self.rate, 
            pitch=self.pitch
        )
        await communicate.save(output_file)

    async def _generate_audio(self, text, output_file):
        # 1. Try ElevenLabs if API key is provided
        if self.eleven_api_key and self.eleven_api_key.strip():
            try:
                success = self._generate_elevenlabs_audio(text, output_file)
                if success:
                    return
            except Exception as e:
                print(f"⚠️ ElevenLabs audio yaratishda xatolik ({e}), Edge TTS-ga o'tilmoqda...")

        # 2. Fallback to Edge TTS
        await self._generate_edge_audio(text, output_file)

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
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                subprocess.run(["afplay", temp_path], check=False)
        except Exception as e:
            print(f"⚠️ TTS Xatosi: {e}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    tts = UzbekTTS()
    tts.speak("Assalomu alaykum! Men Jarvisman, sizga qanday yordam bera olaman?")

