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
    """Detects simple hand gestures using MediaPipe + OpenCV.

    - SWIPE_LEFT: hand moves left
    - SWIPE_UP: hand moves up
    - HAND_UP: sustained raised hand
    """

    def __init__(self, callback: Callable[[GestureEvent], None], camera_index: int = 0):
        self.callback = callback
        self.camera_index = camera_index
        self.running = True

        self.prev_center = None
        self.hand_raised_since: Optional[float] = None
        self.min_raise_duration = 0.2  # seconds
        # Cooldown so HAND_UP doesn't spam every frame
        self.last_hand_up_time = 0.0
        self.hand_up_cooldown = 2.0  # seconds between HAND_UP events


        self.mp_hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.mp_draw = mp.solutions.drawing_utils

    def emit(self, gesture_type: str):
        event = GestureEvent(type=gesture_type, timestamp=time.time())
        self.callback(event)

    def run(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[GestureDetector] First attempt failed, retrying...")
            time.sleep(0.5)
            cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("[GestureDetector] Could not open camera. Gestures disabled.")
            return
        else:
            print("[GestureDetector] Camera opened. Raise your hand, swipe left/up to interact.")

        while self.running:
            ret, frame = cap.read()
            if not ret:
                print("[GestureDetector] Failed to read frame from camera.")
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.mp_hands.process(rgb)

            h, w, _ = frame.shape
            center = None

            if result.multi_hand_landmarks:
                hand_landmarks = result.multi_hand_landmarks[0]
                center = compute_hand_center(hand_landmarks.landmark, w, h)

            if center and self.prev_center:
                is_left, is_up = detect_movement_direction(self.prev_center, center)
                if is_left:
                    self.emit("SWIPE_LEFT")
                elif is_up:
                    self.emit("SWIPE_UP")

                # HAND UP
                                # Hand raised detection with cooldown
                if is_hand_raised(center):
                    if self.hand_raised_since is None:
                        # first frame we see the hand up
                        self.hand_raised_since = time.time()
                    elif time.time() - self.hand_raised_since >= self.min_raise_duration:
                        now = time.time()
                        # only emit if enough time has passed since last HAND_UP
                        if now - self.last_hand_up_time > self.hand_up_cooldown:
                            self.last_hand_up_time = now
                            self.emit("HAND_UP")

                        # reset so we require a fresh raise next time
                        self.hand_raised_since = None
                else:
                    # hand dropped, reset timer
                    self.hand_raised_since = None


            self.prev_center = center

        cap.release()
