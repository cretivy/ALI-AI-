import sys
import torch
import numpy as np
import sounddevice as sd
from transformers import pipeline
import config

class UzbekSTT:
    def __init__(self):
        if config.STT_MODE == "server":
            print("📡 STT Server rejimi faol. Mahalliy model yuklanishi o'tkarib yuborildi.")
            self.device = "server"
            self.pipe = None
            return

        print("⏳ STT Moduli yuklanmoqda (islomov/rubaistt_v2_medium)...")
        # Check Apple Silicon MPS support
        if torch.backends.mps.is_available():
            self.device = "mps"
            print("🚀 Apple Silicon MPS GPU jadallatgichidan foydalanilmoqda!")
        else:
            self.device = "cpu"
            print("💻 CPU rejimidan foydalanilmoqda.")

        try:
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=config.STT_MODEL_NAME,
                device=self.device,
                dtype=torch.float32
            )
            print("✅ STT Moduli muvaffaqiyatli yuklandi!")
        except Exception as e:
            print(f"⚠️ MPS xatosi bo'lsa CPUga o'tilmoqda: {e}")
            self.device = "cpu"
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=config.STT_MODEL_NAME,
                device="cpu"
            )
            print("✅ STT Moduli CPUda yuklandi!")

    def record_audio_vad(self, duration=config.MAX_RECORD_SECONDS, sample_rate=config.SAMPLE_RATE):
        """Microphone capture with Voice Activity Detection (VAD)"""
        import time
        print("\n🎤 Gapiring (Ovoz tinglanmoqda)...")
        recording = []
        
        chunk_duration = 0.1  # 100ms chunks
        chunk_samples = int(sample_rate * chunk_duration)
        
        silence_threshold = config.SILENCE_THRESHOLD
        silence_limit_chunks = int(config.SILENCE_DURATION / chunk_duration)
        
        silence_chunks = 0
        has_spoken = False
        
        try:
            stream = sd.InputStream(samplerate=sample_rate, channels=config.AUDIO_CHANNELS)
            with stream:
                start_time = time.time()
                while time.time() - start_time < duration:
                    data, overflowed = stream.read(chunk_samples)
                    recording.append(data)
                    
                    # Calculate volume (RMS)
                    rms = np.sqrt(np.mean(data**2))
                    
                    # Detect speech activity
                    if rms > silence_threshold:
                        if not has_spoken:
                            has_spoken = True
                            print("🗣️ Ovoz aniqlandi...")
                        silence_chunks = 0
                    else:
                        if has_spoken:
                            silence_chunks += 1
                            
                    # If speaking stopped, exit early
                    if has_spoken and silence_chunks >= silence_limit_chunks:
                        print("🤫 Jimjitlik aniqlandi. Yozib olish to'xtatildi.")
                        break
        except Exception as e:
            print(f"⚠️ Ovoz yozishda xatolik: {e}")
            return None

        if not recording:
            return None

        audio_data = np.concatenate(recording, axis=0).flatten()
        return audio_data

    def transcribe(self, audio_data, sample_rate=config.SAMPLE_RATE):
        """Converts raw audio numpy array to Uzbek text using rubaistt_v2_medium"""
        if audio_data is None or len(audio_data) == 0:
            return ""

        if config.STT_MODE == "server":
            import io
            import soundfile as sf
            import requests
            
            try:
                # Convert numpy array to WAV bytes in memory
                wav_io = io.BytesIO()
                sf.write(wav_io, audio_data, sample_rate, format='WAV', subtype='PCM_16')
                wav_io.seek(0)
                
                # Send request to STT server
                files = {"file": ("audio.wav", wav_io, "audio/wav")}
                r = requests.post(config.STT_SERVER_URL, files=files, timeout=15)
                if r.status_code == 200:
                    return r.json().get("text", "").strip()
                else:
                    print(f"⚠️ STT Server xatoligi: {r.status_code} - {r.text}")
                    return ""
            except Exception as e:
                print(f"⚠️ STT Server ulanish xatoligi: {e}")
                return ""

        # Normalize audio data
        audio_data = audio_data.astype(np.float32)
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))

        inputs = {"raw": audio_data, "sampling_rate": sample_rate}
        result = self.pipe(inputs)
        transcription = result.get("text", "").strip()
        return transcription

if __name__ == "__main__":
    stt = UzbekSTT()
    audio = stt.record_audio_vad(duration=5)
    text = stt.transcribe(audio)
    print(f"📝 Olingan Matn: {text}")
