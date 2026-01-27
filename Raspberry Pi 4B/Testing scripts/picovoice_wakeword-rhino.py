import struct
import subprocess
import numpy as np
from pvrecorder import PvRecorder
import pvporcupine
import pvrhino

# ------------------------
# CONFIG
# ------------------------
ACCESS_KEY = 'cjmNT4hfxmJbe4vq5GRB6UAYw53HP9k7skrEAedIHmx1CllZn8W14Q=='
KEYWORD_PATH = 'Hey-buddy_en_raspberry-pi_v4_0_0.ppn'
CONTEXT_PATH = 'My-Buddy_en_raspberry-pi_v4_0_0.rhn'
USB_MIC_INDEX = 2       # From `arecord -l`
RESPEAKER_DEVICE = 'plughw:3,0'
ALERT_SOUND = '/usr/share/sounds/alsa/Front_Right.wav'

# ------------------------
# INTENT HANDLER
# ------------------------
def handle_intent(intent, slots):
    if intent == "turnLight":
        state = slots.get("state")
        room = slots.get("room")
        print(f"Turning {state} light in {room}")
    elif intent == "setTimer":
        duration = slots.get("duration")
        print(f"Setting timer for {duration}")
    else:
        print("Unknown intent:", intent)

# ------------------------
# MAIN LOOP
# ------------------------
def main():
    # Initialize Porcupine wake word
    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=[KEYWORD_PATH]
    )

    # Initialize Rhino for speech-to-intent
    rhino = pvrhino.create(
        access_key=ACCESS_KEY,
        context_path=CONTEXT_PATH
    )

    # PvRecorder handles microphone input
    recorder = PvRecorder(device_index=USB_MIC_INDEX, frame_length=porcupine.frame_length)
    recorder.start()
    print("Listening for wake word...")

    try:
        while True:
            pcm = recorder.read()  # list of ints

            # Check wake word first
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print("Wake word detected!")
                
                # Now start Rhino inference
                print("Listening for command...")
                rhino_activated = True
                while rhino_activated:
                    pcm_intent = recorder.read()
                    is_finalized = rhino.process(pcm_intent)
                    if is_finalized:
                        inference = rhino.get_inference()
                        if inference.is_understood:
                            print("Intent:", inference.intent)
                            print("Slots:", inference.slots)
                            handle_intent(inference.intent, inference.slots)
                        else:
                            print("Command not understood")
                        rhino_activated = False
                        print("Listening for wake word...")

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        recorder.stop()
        recorder.delete()
        porcupine.delete()
        rhino.delete()

if __name__ == "__main__":
    main()
