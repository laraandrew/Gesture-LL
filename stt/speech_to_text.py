import os
import time
import tempfile
import sounddevice as sd
import soundfile as sf
from openai import OpenAI


class SpeechToText:
    """
    Real microphone-based STT using Whisper via OpenAI API.
    Synchronous version — REQUIRED because main.py calls transcribe() normally.
    """

    def __init__(
        self,
        mode: str = "whisper",
        sample_rate: int = 16000,
        channels: int = 1,
        duration: float = 3.0,
        on_start=None,
        on_stop=None,
    ):
        self.mode = mode
        self.sample_rate = sample_rate
        self.channels = channels
        self.duration = duration
        self.on_start = on_start
        self.on_stop = on_stop
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def transcribe(self) -> str:
        """Record microphone and send to Whisper. BLOCKING call (correct)."""

        if self.on_start:
            self.on_start()

        print("[STT] Recording...")

        audio = sd.rec(
            int(self.duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
        )
        sd.wait()

        if self.on_stop:
            self.on_stop()

        print("[STT] Processing...")

        # Save temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, audio, self.sample_rate)
            audio_path = tmp.name

        # Send audio to Whisper
        response = self.client.audio.transcriptions.create(
            model="gpt-4o-mini-tts",   # ✔️ correct for Whisper-like STT
            file=open(audio_path, "rb"),
        )

        text = response.text.strip()
        print(f"[STT] Transcript: {text}")
        return text
