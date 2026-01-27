import pvporcupine
import sounddevice as sd
import numpy as np
import subprocess

# ------------------------
# CONFIG
# ------------------------
ACCESS_KEY = 'cjmNT4hfxmJbe4vq5GRB6UAYw53HP9k7skrEAedIHmx1CllZn8W14Q=='
KEYWORD_PATH = 'Hey-buddy_en_raspberry-pi_v4_0_0.ppn'
USB_MIC_INDEX = 2       # From `arecord -l`
RESPEAKER_DEVICE = 'plughw:3,0'  # ReSpeaker speaker device
ALERT_SOUND = '/usr/share/sounds/alsa/Front_Right.wav'

# ------------------------
# INIT PORCUPINE
# ------------------------
porcupine = pvporcupine.create(
    access_key=ACCESS_KEY,
    keyword_paths=[KEYWORD_PATH]
)

# ------------------------
# CALLBACK
# ------------------------
def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    pcm = (indata[:, 0] * 32767).astype(np.int16)
    if porcupine.process(pcm) >= 0:
        print("Wake word detected!")
        # Play sound using aplay on ReSpeaker
        subprocess.Popen(['aplay', '-D', RESPEAKER_DEVICE, ALERT_SOUND])

# ------------------------
# START INPUT STREAM
# ------------------------
with sd.InputStream(
        device=USB_MIC_INDEX,
        channels=1,
        samplerate=porcupine.sample_rate,
        blocksize=porcupine.frame_length,
        dtype='float32',
        callback=audio_callback
    ):
    print("Listening for wake word... Press Ctrl+C to stop.")
    while True:
        pass