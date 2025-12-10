import os
os.environ["OPENCV_AVFOUNDATION_SKIP_AUTH"] = "1"
from dotenv import load_dotenv
import asyncio
import threading
import platform
import re
import unicodedata
from typing import Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from word_bank import WORD_BANK
from cv.gesture_detector import GestureDetector, GestureEvent
from stt.speech_to_text import SpeechToText
from ui.flashcard_view import FlashcardView
from ui.animations import Animations

# 🔥 Shared listening state
import core.listening_state as listening_state

load_dotenv()


# -----------------------------------------------------
# Normalization Helpers (NEW)
# -----------------------------------------------------
def normalize_answer(text: str) -> str:
    """Normalize Whisper text for robust comparison."""
    if not text:
        return ""

    # Lowercase & strip
    text = text.lower().strip()

    # Remove leading/trailing punctuation
    text = re.sub(r'^[\.\,\!\?\;\:]+|[\.\,\!\?\;\:]+$', '', text)

    # Remove Whisper japanese punctuation
    text = text.replace("。", "").replace("、", "")

    # Normalize accents → ASCII
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")

    return text.strip()


# -----------------------------------------------------
# Deck Manager
# -----------------------------------------------------
class DeckManager:
    def __init__(self, word_bank: Dict[str, str]):
        self.all_words = list(word_bank.items())
        self.index = 0
        self.word_bank = word_bank

        self.learned_words = []
        self.study_more_words = []
        self.revisit_words = []

        self.current_word = (
            self.all_words[self.index][0] if self.all_words else None
        )
        self.view = FlashcardView()

    def _advance(self):
        if not self.all_words:
            self.current_word = None
            return

        self.index = (self.index + 1) % len(self.all_words)
        self.current_word = self.all_words[self.index][0]
        print(f"[deck] Advanced to index={self.index}, word={self.current_word!r}")

    def mark_study_more(self):
        print(f"[deck] mark_study_more on {self.current_word!r}")
        if self.current_word not in self.study_more_words:
            self.study_more_words.append(self.current_word)
        self._advance()

    def mark_revisit(self):
        print(f"[deck] mark_revisit on {self.current_word!r}")
        if self.current_word not in self.revisit_words:
            self.revisit_words.append(self.current_word)
        self._advance()

    def mark_learned(self):
        print(f"[deck] mark_learned on {self.current_word!r}")
        if self.current_word not in self.learned_words:
            self.learned_words.append(self.current_word)
        self._advance()

    # -----------------------------------------------------
    # UPDATED evaluate_spoken
    # -----------------------------------------------------
    def evaluate_spoken(self, spoken: str) -> bool:
        expected_raw = self.word_bank.get(self.current_word, "")

        cleaned_expected = normalize_answer(expected_raw)
        cleaned_spoken = normalize_answer(spoken)

        # Exact OR fuzzy match
        correct = (
            cleaned_spoken == cleaned_expected
            or cleaned_expected in cleaned_spoken  # fuzzy containment match
        )

        print(
            f"[eval] spoken_raw={spoken!r}, cleaned={cleaned_spoken!r}, "
            f"expected={cleaned_expected!r}, correct={correct}"
        )

        return correct

    def get_state(self) -> Dict[str, Any]:
        return self.view.to_dict(
            current_english=self.current_word,
            current_spanish=self.word_bank.get(self.current_word),
            learned=self.learned_words,
            study_more=self.study_more_words,
            revisit=self.revisit_words,
        )


# -----------------------------------------------------
# WebSocket Manager
# -----------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[ws] Connected. Total={len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"[ws] Disconnected. Total={len(self.active_connections)}")

    async def send(self, websocket: WebSocket, msg: dict):
        try:
            await websocket.send_json(msg)
        except Exception as e:
            print(f"[ws] send failed: {e}")
            self.disconnect(websocket)

    async def broadcast(self, msg: dict):
        for ws in list(self.active_connections):
            await self.send(ws, msg)

    async def broadcast_state(self):
        data = deck_manager.get_state()
        for ws in list(self.active_connections):
            await self.send(ws, {"type": "state", "payload": data})


# -----------------------------------------------------
# FastAPI Setup
# -----------------------------------------------------
app = FastAPI(title="Gesture Language App")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

deck_manager = DeckManager(WORD_BANK)
stt_engine = SpeechToText(mode="whisper", duration=3.0)
animations = Animations()
ws_manager = ConnectionManager()

ASYNC_LOOP = None
gesture_detector = None
gesture_thread_started = False
gesture_thread_lock = threading.Lock()


# -----------------------------------------------------
# Gesture Handler
# -----------------------------------------------------
async def handle_gesture_event(event: GestureEvent):
    print(f"[gesture-handler] Received event: {event.type}")

    if listening_state.is_listening:
        print("[gesture-handler] Ignoring gestures while listening.")
        return

    if event.type == "SWIPE_LEFT":
        deck_manager.mark_revisit()
        await ws_manager.broadcast({"type": "event", "payload": {"kind": "gesture", "name": "SWIPE_LEFT"}})

    elif event.type == "SWIPE_UP":
        deck_manager.mark_study_more()
        await ws_manager.broadcast({"type": "event", "payload": {"kind": "gesture", "name": "SWIPE_UP"}})

    elif event.type == "HAND_UP":
        print("[gesture-handler] HAND_UP → Starting STT")

        listening_state.is_listening = True

        await ws_manager.broadcast({"type": "START_RECORDING"})

        spoken = stt_engine.transcribe()
        print(f"[gesture-handler] Spoken: {spoken}")

        await ws_manager.broadcast({"type": "STOP_RECORDING", "text": spoken})

        # Evaluate
        correct = deck_manager.evaluate_spoken(spoken)

        if correct:
            deck_manager.mark_learned()
            animations.show_correct_animation()
        else:
            deck_manager.mark_revisit()
            animations.show_incorrect_animation()

        await ws_manager.broadcast({
            "type": "event",
            "payload": {"kind": "evaluation", "correct": correct, "spoken": spoken},
        })

        listening_state.is_listening = False

    await ws_manager.broadcast_state()


# -----------------------------------------------------
# Gesture Detector Thread
# -----------------------------------------------------
def start_gesture_detector():
    global gesture_detector, gesture_thread_started

    with gesture_thread_lock:
        if gesture_thread_started:
            print("[gesture] Already running.")
            return

        if ASYNC_LOOP is None:
            print("[gesture] Cannot start — event loop missing.")
            return

        def cb(event: GestureEvent):
            asyncio.run_coroutine_threadsafe(handle_gesture_event(event), ASYNC_LOOP)

        gesture_detector = GestureDetector(cb)
        threading.Thread(target=gesture_detector.run, daemon=True).start()
        gesture_thread_started = True
        print("[gesture] Detector started.")


@app.on_event("startup")
async def startup_event():
    global ASYNC_LOOP
    ASYNC_LOOP = asyncio.get_running_loop()
    start_gesture_detector()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/api/state")
async def get_state():
    return deck_manager.get_state()


def main():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
