"""
File: transcription.py
Purpose: Handles audio transcription using the Whisper model.

Flow:
- Audio file is uploaded via the /transcribe endpoint in main.py.
- This file processes the audio and returns the transcription.
"""

import whisper
import os
from fastapi import UploadFile

# Load the Whisper model
model = whisper.load_model("base")  # You can try "tiny", "small", "medium" too

def transcribe_audio(file_path: str):
    try:
        # Transcribe using Whisper
        result = model.transcribe(file_path)
        return {"text": result["text"]}
    except Exception as e:
        return {"error": str(e)}
