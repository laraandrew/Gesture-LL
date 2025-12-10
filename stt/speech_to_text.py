import os
import tempfile
import sounddevice as sd
import soundfile as sf
from openai import OpenAI


class SpeechToText:
    def __init__(
        self,
        mode: str = "dummy",
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

        if mode == "whisper":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("[STT] WARNING: OPENAI_API_KEY not set. Using dummy mode.")
                self.mode = "dummy"
                self.client = None
            else:
                self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

    def transcribe(self) -> str:
        if self.mode == "dummy":
            print("\n[STT] Dummy mode: type the Spanish word:")
            return input("> ").strip()

        if self.on_start:
            self.on_start()

        print("[STT] Recording…")

        try:
            audio = sd.rec(
                int(self.duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
            )
            sd.wait()
        except Exception as e:
            print(f"[STT] Mic error: {e}")
            if self.on_stop:
                self.on_stop()
            return ""

        if self.on_stop:
            self.on_stop()

        # Save temp WAV
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, audio, self.sample_rate)
                audio_path = tmp.name

            with open(audio_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                )

            return response.text.strip()

        except Exception as e:
            print(f"[STT] Whisper error: {e}")
            return ""

        finally:
            try:
                os.unlink(audio_path)
            except:
                pass
