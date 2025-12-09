DEBUG = True

import time
from dataclasses import dataclass
from typing import Callable, Optional

import cv2
import mediapipe as mp

from .hand_utils import compute_hand_center, detect_movement_direction, is_hand_raised


@dataclass
class GestureEvent:
    type: str
    timestamp: float


class GestureDetector:
    """Detects simple hand gestures using MediaPipe + OpenCV."""

    def debug(self, *args):
        if DEBUG:
            print("[gesture]", *args)

    def __init__(self, callback: Callable[[GestureEvent], None], camera_index: int = 0):
        self.callback = callback
        self.camera_index = camera_index
        self.running = True

        self.prev_center = None
        self.hand_raised_since: Optional[float] = None
        self.min_raise_duration = 0.25  # small buffer

        self.last_hand_up_time = 0.0
        self.hand_up_cooldown = 2.0

        self.mp_hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
        )

    def emit(self, gesture_type: str):
        self.debug("EMIT:", gesture_type)
        self.callback(GestureEvent(type=gesture_type, timestamp=time.time()))

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)

        if not cap.isOpened():
            print("[GestureDetector] ERROR: Could not open camera.")
            return

        print("[GestureDetector] Camera opened. Ready for gestures.")

        while self.running:
            ret, frame = cap.read()
            if not ret:
                print("[gesture] Frame read failed")
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.mp_hands.process(rgb)

            h, w, _ = frame.shape
            center = None

            # -------------------------
            # Hand detection
            # -------------------------
            if result.multi_hand_landmarks:
                hand_landmarks = result.multi_hand_landmarks[0]
                center = compute_hand_center(hand_landmarks.landmark, w, h)

                if center:
                    self.debug("Hand center:", center)
                else:
                    self.debug("Invalid center frame")
            else:
                if self.prev_center is not None:
                    self.debug("Hand lost")
                center = None

            if center is None:
                self.prev_center = None
                self.hand_raised_since = None
                continue

            # -------------------------
            # Swipe detection
            # -------------------------
            if self.prev_center:
                is_left, is_up = detect_movement_direction(self.prev_center, center)

                if is_left:
                    self.debug("SWIPE_LEFT detected")
                    self.emit("SWIPE_LEFT")

                elif is_up:
                    self.debug("SWIPE_UP detected")
                    self.emit("SWIPE_UP")

            # -------------------------
            # Hand-Up detection (Hold)
            # -------------------------
            RAISE_THRESHOLD = 0.22
            is_raised = center.y < RAISE_THRESHOLD

            if is_raised:
                if self.hand_raised_since is None:
                    self.hand_raised_since = time.time()
                    self.debug("Hand raise start")

                elif time.time() - self.hand_raised_since >= self.min_raise_duration:
                    now = time.time()
                    if now - self.last_hand_up_time > self.hand_up_cooldown:
                        self.last_hand_up_time = now
                        self.emit("HAND_UP")
                        self.debug("HAND_UP emitted")

                    self.hand_raised_since = None
            else:
                if self.hand_raised_since is not None:
                    self.debug("Hand lowered")
                self.hand_raised_since = None

            self.prev_center = center

        cap.release()
