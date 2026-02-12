#!/usr/bin/env python3
import picollm
import signal
import sys
from tts_piper import speak

pllm = None

def cleanup(sig=None, frame=None):
    if pllm:
        pllm.interrupt()
        pllm.release()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)

pllm = picollm.create(
    access_key='cjmNT4hfxmJbe4vq5GRB6UAYw53HP9k7skrEAedIHmx1CllZn8W14Q==',
    model_path='/home/visser/python/phi2-307.pllm'
)

system = "You are Buddy, an offline home assistant. Be brief and helpful."

buffer = []

def stream_callback(token):
    print(token, end='', flush=True)
    buffer.append(token)
    
    # Speak when we hit sentence boundaries
    if token in '.!?\n':
        sentence = ''.join(buffer).strip()
        if sentence:
            speak(sentence)
        buffer.clear()

while True:
    try:
        q = input("You: ").strip()
        if q.lower() in ['exit', 'quit']: break
        if not q: continue
        
        print("Buddy: ", end='', flush=True)
        buffer.clear()
        
        pllm.generate(
            prompt=f"{system}\n\nUser: {q}\nBuddy:",
            completion_token_limit=50,
            stop_phrases=['\n'],
            temperature=0,
            stream_callback=stream_callback
        )
        
        # Speak remaining buffer
        if buffer:
            speak(''.join(buffer).strip())
            buffer.clear()
        
        print()
    except (EOFError, KeyboardInterrupt):
        break

cleanup()