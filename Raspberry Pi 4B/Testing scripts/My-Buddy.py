#!/usr/bin/env python3
"""
My Buddy - Hybrid conversational AI assistant with command recognition
Combines picoLLM generative responses with Rhino command intents
"""
import asyncio
import signal
import sys
import time
import RPi.GPIO as GPIO

# Import modules
from modules.wakeword import setup_wakeword
from modules.audio_processor import (
    setup_cobra, setup_recorder, select_microphone
)
from modules.intent_handler import (
    setup_rhino, handle_intent, setup_leds
)
from modules.llm_handler import setup_llm, generate_response
from modules.viam_robot import connect_robot
from pvleopard import create as create_leopard

# CONFIG
# Picovoice
ACCESS_KEY = "cjmNT4hfxmJbe4vq5GRB6UAYw53HP9k7skrEAedIHmx1CllZn8W14Q=="
KEYWORD_PATH = "Hey-buddy_en_raspberry-pi_v4_0_0.ppn"
CONTEXT_PATH = "My-Buddy_en_raspberry-pi_v4_0_0.rhn"
LLM_MODEL_PATH = "/home/visser/python/phi2-307.pllm"

# Viam Robot
ROBOT_ADDRESS = "my-buddy-main.1zxw399cc5.viam.cloud"
API_KEY_ID = "1dd258cc-c05f-4c45-b81a-97731e419e2d"
API_KEY = "nole6vqgb2biwxn535oj1x38et903ihp"

# Audio
MIC_NAME_HINTS = ["PCM2902", "USB", "Audio Codec"]

# LED CONFIG
LED_PINS = {'red': 6, 'green': 5, 'blue': 13}
LED_PWM_FREQ = 1250  # 1.250 kHz
LED_BRIGHTNESS = {
    'red': 1.0,
    'green': 0.40,
    'blue': 1.0,
}

# VAD CONFIG
SILENCE_THRESHOLD = 0.4  # seconds of silence to consider user done (aggressive for noisy environments)
MAX_LISTEN_TIME = 10  # max seconds to listen
SPEECH_ONSET_DELAY = 0.3  # require at least 0.3s of continuous speech before considering it "started"

# LLM CONFIG
SYSTEM_PROMPT = "You are Buddy, an offline home assistant. Be brief and helpful."

# Global state
_cleanup_resources = {
    'porcupine': None,
    'rhino': None,
    'leopard': None,
    'cobra': None,
    'recorder': None,
    'robot': None,
    'pwm_red': None,
    'pwm_green': None,
    'pwm_blue': None,
    'pllm': None,
}


async def cleanup():
    """Cleanup resources and exit"""
    print("\nCleaning up...")
    
    if _cleanup_resources['pllm']:
        _cleanup_resources['pllm'].interrupt()
        _cleanup_resources['pllm'].release()
    if _cleanup_resources['recorder']:
        _cleanup_resources['recorder'].stop()
        _cleanup_resources['recorder'].delete()
    if _cleanup_resources['porcupine']:
        _cleanup_resources['porcupine'].delete()
    if _cleanup_resources['rhino']:
        _cleanup_resources['rhino'].delete()
    if _cleanup_resources['leopard']:
        _cleanup_resources['leopard'].delete()
    if _cleanup_resources['cobra']:
        _cleanup_resources['cobra'].delete()
    
    # Cleanup LEDs
    if _cleanup_resources['pwm_red']:
        _cleanup_resources['pwm_red'].stop()
    if _cleanup_resources['pwm_green']:
        _cleanup_resources['pwm_green'].stop()
    if _cleanup_resources['pwm_blue']:
        _cleanup_resources['pwm_blue'].stop()
    GPIO.cleanup()
    
    # Close robot connection
    if _cleanup_resources['robot']:
        await _cleanup_resources['robot'].close()


async def listen_for_speech(recorder, cobra):
    """
    Listen for user speech using VAD
    
    Returns:
        List of audio samples (raw from microphone)
    """
    audio_frames = []
    silence_duration = 0
    speech_duration = 0  # track how long speech has been detected
    start_time = time.time()
    speaking = False
    speech_started = False  # only count silence after speech clearly starts
    
    while True:
        pcm = recorder.read()
        
        # Add raw PCM directly (skip Koala for noisy environments)
        audio_frames.extend(pcm)
        
        # Check if voice activity detected (Cobra needs 512 samples)
        if cobra.process(pcm):
            if not speaking:
                print("🎙️ Speech detected...", end='', flush=True)
                speaking = True
                speech_duration = 0
            
            # Accumulate speech duration
            speech_duration += len(pcm) / cobra.sample_rate
            
            # Mark speech as "started" once we have enough continuous speech
            if speech_duration >= SPEECH_ONSET_DELAY:
                speech_started = True
            
            silence_duration = 0
        else:
            if speaking:
                print("", end='', flush=True)  # newline after speech indicator
                speaking = False
            
            # Only count silence if speech has clearly started
            if speech_started:
                silence_duration += len(pcm) / cobra.sample_rate
                print(f"(silence: {silence_duration:.1f}s)", end='\r', flush=True)
                
                if silence_duration >= SILENCE_THRESHOLD:
                    print()  # newline before breaking
                    break
        
        # Fallback: stop listening after max time
        if time.time() - start_time >= MAX_LISTEN_TIME:
            print(f"\n(max listen time reached)")
            break
    
    return audio_frames


async def main():
    """Main application loop"""
    # signal.signal(signal.SIGINT, cleanup)
    
    print("=== My Buddy Startup ===\n")
    
    # Setup audio components
    print("Setting up audio...")
    mic_index = select_microphone(MIC_NAME_HINTS)
    cobra = setup_cobra(ACCESS_KEY)
    
    _cleanup_resources['cobra'] = cobra
    
    # Setup Picovoice engines
    print("Setting up Picovoice engines...")
    porcupine = setup_wakeword(ACCESS_KEY, KEYWORD_PATH)
    rhino = setup_rhino(ACCESS_KEY, CONTEXT_PATH)
    leopard = create_leopard(access_key=ACCESS_KEY)
    pllm = setup_llm(ACCESS_KEY, LLM_MODEL_PATH)
    
    _cleanup_resources['porcupine'] = porcupine
    _cleanup_resources['rhino'] = rhino
    _cleanup_resources['leopard'] = leopard
    _cleanup_resources['pllm'] = pllm
    
    # Setup recorder
    recorder = setup_recorder(mic_index, porcupine.frame_length)
    _cleanup_resources['recorder'] = recorder
    
    # Setup LEDs
    print("Setting up LEDs...")
    pwm_red, pwm_green, pwm_blue = setup_leds(LED_PINS, LED_PWM_FREQ)
    
    _cleanup_resources['pwm_red'] = pwm_red
    _cleanup_resources['pwm_green'] = pwm_green
    _cleanup_resources['pwm_blue'] = pwm_blue
    
    # Connect to robot
    print("Connecting to robot...")
    robot = await connect_robot(ROBOT_ADDRESS, API_KEY_ID, API_KEY)
    _cleanup_resources['robot'] = robot
    
    print("\n✓ All systems ready")
    print("Listening for 'Hey Buddy'...\n")
    
    # Main loop
    conversation_active = False
    conversation_expires_at = 0
    wakeword_cooldown = 300  # seconds
    
    try:
        while True:
            pcm = recorder.read()
            now = time.time()
            
            # ---- SLEEP MODE ----
            if not conversation_active:
                if porcupine.process(pcm) >= 0:
                    print("\n🎤 Wake word detected!")
                    conversation_active = True
                    conversation_expires_at = now + wakeword_cooldown
                    from tts_piper import speak
                                        
                    try:
                        # Listen for speech with VAD
                        print("Listening for speech...")
                        audio_frames = await listen_for_speech(recorder, cobra)
                        
                        if not audio_frames:
                            print("No speech detected")
                            conversation_active = False
                            continue
                        
                        # Try to recognize intent with Rhino
                        intent_found = False
                        try:
                            # Chunk audio frames into Rhino's frame_length
                            rhino_frame_length = rhino.frame_length
                            for i in range(0, len(audio_frames), rhino_frame_length):
                                rhino_frame = audio_frames[i:i + rhino_frame_length]
                                
                                # Skip incomplete frames
                                if len(rhino_frame) < rhino_frame_length:
                                    break
                                
                                if not rhino.process(rhino_frame):
                                    continue
                                inference = rhino.get_inference()
                                if inference.intent:
                                    print(f"\n📋 Intent: {inference.intent}")
                                    if inference.slots:
                                        print(f"   Slots: {inference.slots}")
                                    
                                    # Handle the intent
                                    await handle_intent(
                                        inference.intent, 
                                        inference.slots, 
                                        robot,
                                        pwm_red, pwm_green, pwm_blue,
                                        LED_BRIGHTNESS
                                    )
                                    intent_found = True
                                    break
                        except Exception as e:
                            print(f"Error processing intent: {e}")
                        
                        # If no intent matched, use LLM for conversation
                        if not intent_found:
                            try:
                                print("Processing with LLM...")
                                transcript, _ = leopard.process(audio_frames)
                                if transcript.strip():
                                    print(f"You said: {transcript}")
                                    generate_response(pllm, transcript, SYSTEM_PROMPT)
                                else:
                                    print("Could not transcribe speech")
                            except Exception as e:
                                print(f"Error with LLM: {e}")
                        
                    except Exception as e:
                        print(f"Error during speech handling: {e}")
                    
                    conversation_active = False
                    print("\nListening for 'Hey Buddy'...\n")
                    continue
            
            # Conversation timeout
            if now > conversation_expires_at:
                conversation_active = False
    
    except KeyboardInterrupt:
        pass
    
    finally:
        await cleanup()


if __name__ == "__main__":
    asyncio.run(main())
