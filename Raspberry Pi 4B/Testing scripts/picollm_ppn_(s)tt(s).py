#!/usr/bin/env python3
import picollm
import signal
import sys
import time
import threading
from tts_piper import speak
from pvrecorder import PvRecorder
# Picovoice modules
import pvporcupine
import pvleopard
import pvkoala
import pvcobra

# CONFIG
ACCESS_KEY = "cjmNT4hfxmJbe4vq5GRB6UAYw53HP9k7skrEAedIHmx1CllZn8W14Q=="
KEYWORD_PATH = "Hey-buddy_en_raspberry-pi_v4_0_0.ppn"
MODEL_PATH = "/home/visser/python/phi2-307.pllm"
MIC_NAME_HINTS = ["PCM2902", "USB", "Audio Codec"]
LISTEN_DURATION = 5  # seconds to listen for user speech

pllm = None
recorder = None
porcupine = None
leopard = None
koala = None
cobra = None

def cleanup(sig=None, frame=None):
    if pllm:
        pllm.interrupt() 
        pllm.release() # Pico LLM
    if recorder:
        recorder.stop()
        recorder.delete() # Record voice
    if porcupine:
        porcupine.delete() # wakeword
    if leopard:
        leopard.delete() # Speech To Text
    if koala:
        koala.delete() # Cancel out background noise
    if cobra:
        cobra.delete() # Voice Activity Detection
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)

# Setup LLM
pllm = picollm.create(
    access_key=ACCESS_KEY,
    model_path=MODEL_PATH
)

# Setup Leopard STT
leopard = pvleopard.create(access_key=ACCESS_KEY)

# Setup Koala Noise Suppression
koala = pvkoala.create(access_key=ACCESS_KEY)

# Setup Cobra Voice Activity Detection
cobra = pvcobra.create(access_key=ACCESS_KEY)

system = "You are Buddy, an offline home assistant. Be brief and helpful."

# Setup wake word
porcupine = pvporcupine.create(
    access_key=ACCESS_KEY,
    keyword_paths=[KEYWORD_PATH],
)

# Setup microphone
devices = PvRecorder.get_available_devices()
mic_index = None

for i, d in enumerate(devices):
    if "monitor" in d.lower():
        continue
    if any(hint.lower() in d.lower() for hint in MIC_NAME_HINTS):
        mic_index = i
        break

if mic_index is None:
    for i, d in enumerate(devices):
        if "monitor" not in d.lower():
            mic_index = i
            break

if mic_index is None:
    raise RuntimeError("No microphone found")

print(f"Using mic: {devices[mic_index]}")

recorder = PvRecorder(
    device_index=mic_index,
    frame_length=porcupine.frame_length,
)
recorder.start()

print("Listening for 'Hey Buddy'...")

buffer = []

def stream_callback(token):
    print(token, end='', flush=True)
    buffer.append(token)
    
    if token in '.!?\n':
        sentence = ''.join(buffer).strip()
        if sentence:
            threading.Thread(target=speak, args=(sentence,), daemon=True).start()
        buffer.clear()

# Main loop
try:
    while True:
        pcm = recorder.read() # "Read" audio
        
        if porcupine.process(pcm) >= 0:
            print("\nWake word detected!")
            
            # Record user speech with VAD (Voice Activity Detection)
            print("Listening...")
            audio_frames = []
            silence_duration = 0
            silence_threshold = 1.5  # seconds of silence to consider user done (increased for noisy environments)
            max_listen_time = 10  # max seconds to listen as fallback
            frame_buffer = []  # Buffer to align frame sizes
            start_time = time.time()
            
            while True:
                pcm = recorder.read()
                frame_buffer.extend(pcm)
                
                # Process frames in Koala's frame_length chunks
                while len(frame_buffer) >= koala.frame_length:
                    koala_frame = frame_buffer[:koala.frame_length]
                    frame_buffer = frame_buffer[koala.frame_length:]
                    
                    # Clean audio through Koala noise suppression
                    enhanced_pcm = koala.process(koala_frame)
                    audio_frames.extend(enhanced_pcm)
                
                # Check if voice activity detected (Cobra needs 512 samples)
                if len(pcm) == cobra.frame_length:
                    if cobra.process(pcm):
                        silence_duration = 0
                    else:
                        silence_duration += len(pcm) / cobra.sample_rate
                        
                        if silence_duration >= silence_threshold:
                            break
                
                # Fallback: stop listening after max time
                if time.time() - start_time >= max_listen_time:
                    break
            
            # Use leopard for Speech To Text
            print("Processing speech...")
            transcript, _ = leopard.process(audio_frames)
            
            # Reset Koala for next recording
            koala.reset()
            
            q = transcript.strip()
            print(f"You said: {q}")
            
            if not q:
                speak("I didn't hear anything")
                continue
            
            print("Buddy: ", end='', flush=True)
            buffer.clear()
            
            # Generate response
            pllm.generate(
                prompt=f"{system}\n\nUser: {q}\nBuddy:",
                completion_token_limit=50,
                stop_phrases=['\n'],
                temperature=0,
                stream_callback=stream_callback
            )
            
            # Speak
            if buffer:
                sentence = ''.join(buffer).strip()
                if sentence:
                    threading.Thread(target=speak, args=(sentence,), daemon=True).start()
                buffer.clear()
            
            print("\n")
            print("Listening for 'Hey Buddy'...")

except KeyboardInterrupt:
    pass

cleanup()