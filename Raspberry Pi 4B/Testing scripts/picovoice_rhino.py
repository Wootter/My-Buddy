import pvrhino
from pvrecorder import PvRecorder

ACCESS_KEY = 'cjmNT4hfxmJbe4vq5GRB6UAYw53HP9k7skrEAedIHmx1CllZn8W14Q=='
CONTEXT_PATH = 'My-Buddy_en_raspberry-pi_v4_0_0.rhn'
USB_MIC_INDEX = 2

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

def main():
    rhino = pvrhino.create(access_key=ACCESS_KEY, context_path=CONTEXT_PATH)

    recorder = PvRecorder(device_index=USB_MIC_INDEX, frame_length=rhino.frame_length)
    recorder.start()
    print("Listening for commands...")

    try:
        while True:
            pcm = recorder.read()  # Already a list of integers
            is_finalized = rhino.process(pcm)
            if is_finalized:
                inference = rhino.get_inference()
                if inference.is_understood:
                    print("Intent:", inference.intent)
                    print("Slots:", inference.slots)
                    handle_intent(inference.intent, inference.slots)
                else:
                    print("Command not understood")
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        recorder.stop()
        recorder.delete()
        rhino.delete()

if __name__ == "__main__":
    main()