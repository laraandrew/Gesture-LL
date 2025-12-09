import os
os.environ["OPENCV_AVFOUNDATION_SKIP_AUTH"] = "1"

import asyncio
import threading
import time
import platform
from typing import Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import cv2

from word_bank import WORD_BANK
from cv.gesture_detector import GestureDetector, GestureEvent
from stt.speech_to_text import SpeechToText
from ui.flashcard_view import FlashcardView
from ui.animations import Animations


class DeckManager:
    """Manages flashcard deck and word categories."""
    def __init__(self, word_bank: Dict[str, str]):
        self.all_words = list(word_bank.items())
        self.index = 0
        self.word_bank = word_bank

        self.learned_words = []
        self.study_more_words = []
        self.revisit_words = []

        self.current_word = self.all_words[self.index][0] if self.all_words else None
        self.view = FlashcardView()

    def _advance(self):
        if not self.all_words:
            self.current_word = None
            return
        self.index = (self.index + 1) % len(self.all_words)
        self.current_word = self.all_words[self.index][0]

    def mark_study_more(self):
        if self.current_word and self.current_word not in self.study_more_words:
            self.study_more_words.append(self.current_word)
        self._advance()

    def mark_revisit(self):
        if self.current_word and self.current_word not in self.revisit_words:
            self.revisit_words.append(self.current_word)
        self._advance()

    def mark_learned(self):
        if self.current_word and self.current_word not in self.learned_words:
            self.learned_words.append(self.current_word)
        self._advance()

    def evaluate_spoken(self, spoken: str) -> bool:
        expected = self.word_bank.get(self.current_word, "").lower()
        return spoken.lower().strip() == expected.strip()

    def get_state(self) -> Dict[str, Any]:
        return self.view.to_dict(
            current_english=self.current_word,
            current_spanish=self.word_bank.get(self.current_word),
            learned=self.learned_words,
            study_more=self.study_more_words,
            revisit=self.revisit_words,
        )


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send(self, websocket: WebSocket, msg: dict):
        try:
            await websocket.send_json(msg)
        except:
            self.disconnect(websocket)

    async def broadcast_state(self):
        state = deck_manager.get_state()
        for ws in list(self.active_connections):
            await self.send(ws, {"type": "state", "payload": state})


app = FastAPI(title="Gesture Language Learning App")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

deck_manager = DeckManager(WORD_BANK)
stt_engine = SpeechToText()
animations = Animations()
ws_manager = ConnectionManager()

ASYNC_LOOP = None
gesture_detector = None


def request_camera_permission():
    print("[startup] Requesting camera access on main thread...")
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("[startup] Camera successfully opened.")
        cap.release()
    print("[startup] Camera permission check complete.")


async def handle_gesture_ws(event: GestureEvent, websocket: WebSocket):
    """Async gesture → WebSocket → frontend → STT → evaluation flow."""

    if event.type == "SWIPE_LEFT":
        deck_manager.mark_revisit()
        await ws_manager.send(websocket, {"type": "event", "payload": {"kind": "gesture", "name": "SWIPE_LEFT"}})

    elif event.type == "SWIPE_UP":
        deck_manager.mark_study_more()
        await ws_manager.send(websocket, {"type": "event", "payload": {"kind": "gesture", "name": "SWIPE_UP"}})

    elif event.type == "HAND_UP":
        # 1️⃣ Notify frontend to show "recording"
        await ws_manager.send(websocket, {"type": "START_RECORDING"})

        # 2️⃣ Mock STT (simulate audio → text)
        spoken = stt_engine.transcribe()

        # 3️⃣ Notify frontend to stop recording display
        await ws_manager.send(websocket, {"type": "STOP_RECORDING", "text": spoken})

        # 4️⃣ Evaluate correctness
        correct = deck_manager.evaluate_spoken(spoken)
        if correct:
            animations.show_correct_animation()
        else:
            animations.show_incorrect_animation()

        await ws_manager.send(
            websocket,
            {"type": "event", "payload": {"kind": "evaluation", "correct": correct, "spoken": spoken}},
        )

    # Always send updated deck state
    await ws_manager.broadcast_state()


@app.on_event("startup")
async def startup_event():
    global ASYNC_LOOP, gesture_detector
    ASYNC_LOOP = asyncio.get_running_loop()

    if platform.system() == "Darwin":
        request_camera_permission()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

    # Gesture → WS callback
    def gesture_callback(event: GestureEvent):
        asyncio.run_coroutine_threadsafe(handle_gesture_ws(event, websocket), ASYNC_LOOP)

    # Start detector thread
    threading.Thread(target=lambda: GestureDetector(gesture_callback).run(), daemon=True).start()

    # WS receive loop
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


def main():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
