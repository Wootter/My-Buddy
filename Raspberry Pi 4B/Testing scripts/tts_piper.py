# tts_piper.py
import subprocess
import threading
import sys
import os
from queue import Queue
import time

PIPER_MODEL = "/home/visser/python/en_GB-alan-medium.onnx"
PIPER_CONFIG = "/home/visser/python/en_GB-alan-medium.onnx.json"

class PiperTTS:
    def __init__(self):
        self.proc = subprocess.Popen(
            [
                "stdbuf", "-o0",
                "piper",
                "--model", PIPER_MODEL,
                "--config", PIPER_CONFIG,
                "--output-raw",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

        self.audio = subprocess.Popen(
            ["aplay", "-q", "-f", "S16_LE", "-r", "44100", "-c", "1"],
            stdin=self.proc.stdout,
            stderr=subprocess.DEVNULL,
        )

        self.queue = Queue()
        self.lock = threading.Lock()
        
        # Start the queue processor thread
        self.processor_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.processor_thread.start()
    
    def _process_queue(self):
        """Process text from queue one at a time"""
        while True:
            text = self.queue.get()
            if text is None:
                break
            with self.lock:
                self.proc.stdin.write((text + "\n").encode("utf-8"))
                self.proc.stdin.flush()
            self.queue.task_done()

    def speak(self, text: str):
        if not text:
            return
        self.queue.put(text)

tts = PiperTTS()

def speak(text: str):
    tts.speak(text)
