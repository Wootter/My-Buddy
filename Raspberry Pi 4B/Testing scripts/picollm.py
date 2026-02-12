#!/usr/bin/env python3
import picollm
import signal
import sys

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

while True:
    try:
        q = input("You: ").strip()
        if q.lower() in ['exit', 'quit']: break
        if not q: continue
        
        print("Buddy: ", end='', flush=True)
        pllm.generate(
            prompt=f"{system}\n\nUser: {q}\nBuddy:",
            completion_token_limit=50,
            stop_phrases=['\n'],
            temperature=0,
            stream_callback=lambda t: print(t, end='', flush=True)
        )
        print()
    except (EOFError, KeyboardInterrupt):
        break

cleanup()