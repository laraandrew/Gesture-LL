import time
from typing import Optional


class SpeechToText:
    """
    Dummy speech-to-text used for demo purposes.
    Replace later with Whisper/OpenAI microphone STT.
    """

    def __init__(self, mode: str = "dummy"):
        self.mode = mode

    def transcribe(self) -> str:
        print("[STT] Simulating speech recognition...")
        time.sleep(2)  # Simulate recording time
        return "hola"  # Mock output
#adding to be able to commit