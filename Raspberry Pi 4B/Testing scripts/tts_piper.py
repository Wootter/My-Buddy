# tts_piper.py
import subprocess
import threading
import sys

PIPER_MODEL = "/home/visser/python/en_GB-alan-medium.onnx"
PIPER_CONFIG = "/home/visser/python/en_GB-alan-medium.onnx.json"

class PiperTTS:
    def __init__(self):
        self.proc = subprocess.Popen(
            [
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
            ["aplay", "-q", "-f", "S16_LE", "-r", "22050", "-c", "1"],
            stdin=self.proc.stdout,
            stderr=subprocess.DEVNULL,
        )

        self.lock = threading.Lock()

    def speak(self, text: str):
        if not text:
            return
        with self.lock:
            self.proc.stdin.write((text + "\n").encode("utf-8"))
            self.proc.stdin.flush()

tts = PiperTTS()

def speak(text: str):
    tts.speak(text)
