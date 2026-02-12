#!/usr/bin/env python3
import pvleopard
from pvrecorder import PvRecorder
import time

ACCESS_KEY = "cjmNT4hfxmJbe4vq5GRB6UAYw53HP9k7skrEAedIHmx1CllZn8W14Q=="

# Create Leopard instance
leopard = pvleopard.create(access_key=ACCESS_KEY)

# Setup microphone
devices = PvRecorder.get_available_devices()
print("Available devices:")
for i, d in enumerate(devices):
    print(f"{i}: {d}")

# Use first non-monitor device
mic_index = None
for i, d in enumerate(devices):
    if "monitor" not in d.lower():
        mic_index = i
        break

print(f"\nUsing mic: {devices[mic_index]}")
print("Recording for 5 seconds... speak now!")

recorder = PvRecorder(device_index=mic_index, frame_length=512)
recorder.start()

# Record audio for 5 seconds
audio_frames = []
start = time.time()
while time.time() - start < 5:
    audio_frames.extend(recorder.read())

recorder.stop()
recorder.delete()

print("Processing audio...")

# Transcribe
transcript, words = leopard.process(audio_frames)

print(f"\nTranscript: {transcript}")
print(f"\nWord timings:")
for word in words:
    print(f"  {word.word} ({word.start_sec:.2f}s - {word.end_sec:.2f}s)")

leopard.delete()