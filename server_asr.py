import os
import tempfile
import torch
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from transformers import pipeline
import uvicorn

app = FastAPI(title="Jarvis Uzbek STT Server (rubaistt_v2_medium)")

# Check GPU support
device = "cuda" if torch.cuda.is_available() else "cpu"
if device == "cpu" and torch.backends.mps.is_available():
    device = "mps"

print(f"🚀 STT Model is loading on device: {device}...")
try:
    pipe = pipeline(
        "automatic-speech-recognition",
        model="islomov/rubaistt_v2_medium",
        device=device,
        dtype=torch.float16 if device == "cuda" else torch.float32
    )
    print("✅ STT Model loaded successfully!")
except Exception as e:
    print(f"⚠️ Error loading model: {e}. Falling back to CPU...")
    pipe = pipeline(
        "automatic-speech-recognition",
        model="islomov/rubaistt_v2_medium",
        device="cpu"
    )
    print("✅ STT Model loaded on CPU!")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Receives binary WAV audio file and transcribes it to Uzbek text"""
    try:
        # Read uploaded bytes
        audio_bytes = await file.read()
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_path = temp_audio.name
            
        # Run transcription pipeline
        # HuggingFace pipeline can read filepaths directly!
        result = pipe(temp_path)
        transcription = result.get("text", "").strip()
        
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return {"text": transcription}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "healthy", "device": device}

if __name__ == "__main__":
    # Start the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
