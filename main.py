import os
os.environ["OPENCV_AVFOUNDATION_SKIP_AUTH"] = "1"

from dotenv import load_dotenv
import asyncio
import threading
import re
import unicodedata
from typing import Dict, Any

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
# Normalization Helpers
# -----------------------------------------------------
def normalize_answer(text: str) -> str:
    if not text:
        return ""

    text = text.lower().strip()

    text = re.sub(r'^[\.\,\!\?\;\:]+|[\.\,\!\?\;\:]+$', '', text)
    text = text.replace("。", "").replace("、", "")

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")

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

        self.current_word = self.all_words[self.index][0]
        self.view = FlashcardView()

    def _advance(self):
        self.index = (self.index + 1) % len(self.all_words)
        self.current_word = self.all_words[self.index][0]
        print(f"[deck] Advanced → {self.current_word}")

    def mark_study_more(self):
        self.study_more_words.append(self.current_word)
        self._advance()

    def mark_revisit(self):
        self.revisit_words.append(self.current_word)
        self._advance()

    def mark_learned(self):
        self.learned_words.append(self.current_word)
        self._advance()

    def evaluate_spoken(self, spoken: str) -> bool:
        expected = normalize_answer(self.word_bank[self.current_word])
        spoken_clean = normalize_answer(spoken)

        correct = spoken_clean == expected or expected in spoken_clean

        print(
            f"[eval] spoken_raw={spoken!r}, cleaned={spoken_clean!r}, "
            f"expected={expected!r}, correct={correct}"
        )

        return correct

    def get_state(self):
        return self.view.to_dict(
            current_english=self.current_word,
            current_spanish=self.word_bank[self.current_word],
            learned=self.learned_words,
            study_more=self.study_more_words,
            revisit=self.revisit_words,
        )


# -----------------------------------------------------
# WebSocket Manager
# -----------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, msg: dict):
        for ws in list(self.active):
            try:
                await ws.send_json(msg)
            except:
                self.disconnect(ws)

    async def broadcast_state(self):
        await self.broadcast({
            "type": "state",
            "payload": deck_manager.get_state()
        })


# -----------------------------------------------------
# App Setup
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
    print(f"[gesture-handler] Received: {event.type}")

    if listening_state.is_listening:
        return

    if event.type == "SWIPE_LEFT":
        deck_manager.mark_revisit()
        await ws_manager.broadcast({
            "type": "event",
            "payload": {"kind": "gesture", "name": "SWIPE_LEFT"}
        })

    elif event.type == "SWIPE_UP":
        deck_manager.mark_study_more()
        await ws_manager.broadcast({
            "type": "event",
            "payload": {"kind": "gesture", "name": "SWIPE_UP"}
        })

    elif event.type == "HAND_UP":
        listening_state.is_listening = True

        # ✅ THIS IS THE CRITICAL FIX
        await ws_manager.broadcast({
            "type": "event",
            "payload": {"kind": "gesture", "name": "HAND_UP"}
        })

        await ws_manager.broadcast({"type": "START_RECORDING"})

        loop = asyncio.get_running_loop()
        spoken = await loop.run_in_executor(None, stt_engine.transcribe)


        await ws_manager.broadcast({
            "type": "STOP_RECORDING",
            "text": spoken
        })

        correct = deck_manager.evaluate_spoken(spoken)

        if correct:
            deck_manager.mark_learned()
            animations.show_correct_animation()
        else:
            deck_manager.mark_revisit()
            animations.show_incorrect_animation()

        await ws_manager.broadcast({
            "type": "event",
            "payload": {
                "kind": "evaluation",
                "correct": correct,
                "spoken": spoken
            }
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
            return

        def cb(event: GestureEvent):
            asyncio.run_coroutine_threadsafe(
                handle_gesture_event(event),
                ASYNC_LOOP
            )

        gesture_detector = GestureDetector(cb)
        threading.Thread(
            target=gesture_detector.run,
            daemon=True
        ).start()

        gesture_thread_started = True
        print("[gesture] Detector started")


@app.on_event("startup")
async def startup():
    global ASYNC_LOOP
    ASYNC_LOOP = asyncio.get_running_loop()
    start_gesture_detector()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)


@app.get("/api/state")
async def get_state():
    return deck_manager.get_state()


def main():
    uvicorn.run("main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
