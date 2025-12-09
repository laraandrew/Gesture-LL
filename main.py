import os
os.environ["OPENCV_AVFOUNDATION_SKIP_AUTH"] = "1"
from dotenv import load_dotenv
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


load_dotenv()
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
        print(f"[deck] Advanced to index={self.index}, word={self.current_word!r}")

    def mark_study_more(self):
        print(f"[deck] mark_study_more on {self.current_word!r}")
        if self.current_word and self.current_word not in self.study_more_words:
            self.study_more_words.append(self.current_word)
        self._advance()

    def mark_revisit(self):
        print(f"[deck] mark_revisit on {self.current_word!r}")
        if self.current_word and self.current_word not in self.revisit_words:
            self.revisit_words.append(self.current_word)
        self._advance()

    def mark_learned(self):
        print(f"[deck] mark_learned on {self.current_word!r}")
        if self.current_word and self.current_word not in self.learned_words:
            self.learned_words.append(self.current_word)
        self._advance()

    def evaluate_spoken(self, spoken: str) -> bool:
        expected = self.word_bank.get(self.current_word, "").lower()
        result = spoken.lower().strip() == expected.strip()
        print(f"[eval] spoken={spoken!r}, expected={expected!r}, correct={result}")
        return result

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
        print(f"[ws] Connected. Total={len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"[ws] Disconnected. Total={len(self.active_connections)}")

    async def send(self, websocket: WebSocket, msg: dict):
        try:
            await websocket.send_json(msg)
        except Exception as e:
            print(f"[ws] send failed, dropping connection: {e}")
            self.disconnect(websocket)

    async def broadcast(self, msg: dict):
        """Broadcast a JSON message to all active clients."""
        for ws in list(self.active_connections):
            await self.send(ws, msg)

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

ASYNC_LOOP: Optional[asyncio.AbstractEventLoop] = None
gesture_detector: Optional[GestureDetector] = None
gesture_thread_started = False
gesture_thread_lock = threading.Lock()


def request_camera_permission():
    print("[startup] Requesting camera access on main thread...")
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("[startup] Camera successfully opened.")
        cap.release()
    else:
        print("[startup] WARNING: Could not open camera during permission check.")
    print("[startup] Camera permission check complete.")


async def handle_gesture_event(event: GestureEvent):
    """Async handler for gestures → deck mutations → WS broadcast."""
    print(f"[gesture-handler] Received event: {event.type} @ {event.timestamp}")

    if event.type == "SWIPE_LEFT":
        deck_manager.mark_revisit()
        await ws_manager.broadcast(
            {"type": "event", "payload": {"kind": "gesture", "name": "SWIPE_LEFT"}}
        )

    elif event.type == "SWIPE_UP":
        deck_manager.mark_study_more()
        await ws_manager.broadcast(
            {"type": "event", "payload": {"kind": "gesture", "name": "SWIPE_UP"}}
        )

    elif event.type == "HAND_UP":
        print("[gesture-handler] HAND_UP → starting STT flow")
        # 1️⃣ Notify frontend to show "recording"
        await ws_manager.broadcast({"type": "START_RECORDING"})

        # 2️⃣ STT (mock or real)
        spoken = stt_engine.transcribe()
        print(f"[gesture-handler] STT result: {spoken!r}")

        # 3️⃣ Notify frontend to stop recording display
        await ws_manager.broadcast({"type": "STOP_RECORDING", "text": spoken})

        # 4️⃣ Evaluate correctness
        correct = deck_manager.evaluate_spoken(spoken)
        if correct:
            animations.show_correct_animation()
        else:
            animations.show_incorrect_animation()

        await ws_manager.broadcast(
            {
                "type": "event",
                "payload": {"kind": "evaluation", "correct": correct, "spoken": spoken},
            }
        )

    # Always send updated deck state
    await ws_manager.broadcast_state()


def start_gesture_detector():
    """Start a single global GestureDetector thread (idempotent)."""
    global gesture_detector, gesture_thread_started

    with gesture_thread_lock:
        if gesture_thread_started:
            print("[gesture] GestureDetector already running, skip start.")
            return

        if ASYNC_LOOP is None:
            print("[gesture] ERROR: ASYNC_LOOP is None, cannot start detector yet.")
            return

        def gesture_callback(event: GestureEvent):
            # Called from detector thread
            if ASYNC_LOOP is None:
                print("[gesture-callback] No ASYNC_LOOP, dropping event.")
                return
            try:
                asyncio.run_coroutine_threadsafe(
                    handle_gesture_event(event), ASYNC_LOOP
                )
            except Exception as e:
                print(f"[gesture-callback] Error scheduling coroutine: {e}")

        print("[gesture] Starting GestureDetector thread...")
        gesture_detector = GestureDetector(gesture_callback)
        t = threading.Thread(target=gesture_detector.run, daemon=True)
        t.start()
        gesture_thread_started = True
        print("[gesture] GestureDetector thread started.")


@app.on_event("startup")
async def startup_event():
    global ASYNC_LOOP
    ASYNC_LOOP = asyncio.get_running_loop()
    print("[startup] Async loop captured.")

    if platform.system() == "Darwin":
        request_camera_permission()

    # Start the global gesture detector once at startup
    start_gesture_detector()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

    # WS receive loop – we don't care about client messages yet,
    # but this keeps the connection alive and lets us hook into future commands.
    try:
        while True:
            msg = await websocket.receive_text()
            print(f"[ws] Received from client: {msg!r}")
            # In the future, you can handle explicit client commands here.
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"[ws] Error in websocket loop: {e}")
        ws_manager.disconnect(websocket)


@app.get("/api/state")
async def get_state():
    """Simple debug endpoint so frontend can poll /api/state without 404."""
    state = deck_manager.get_state()
    print("[api/state] State requested.")
    return state


def main():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
