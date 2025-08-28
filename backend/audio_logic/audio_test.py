import whisper

model = whisper.load_model("tiny")
result = model.transcribe(r"C:\Users\Thameem Ansari\Desktop\simplified_final\simplified_version_ai_mental_health\backend\audio_logic\sample_audio\audio1.m4a")
print(result["text"])
