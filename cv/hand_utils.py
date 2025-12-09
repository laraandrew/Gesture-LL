from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class HandPosition:
    x: float  # normalized [0–1]
    y: float  # normalized [0–1]


def compute_hand_center(landmarks, image_width: int, image_height: int) -> Optional[HandPosition]:
    """
    Compute a stable hand center using MediaPipe's normalized landmarks.

    FIXES:
    - Ensures landmarks list is valid (MediaPipe sometimes returns empty structs).
    - Correctly computes average center.
    - Prevents returning invalid values (None, NaN).
    """
    if not landmarks:
        return None

    xs = []
    ys = []

    for lm in landmarks:
        # Some MP versions produce out-of-range values briefly during hand entry/exit
        if 0 <= lm.x <= 1 and 0 <= lm.y <= 1:
            xs.append(lm.x)
            ys.append(lm.y)

    if not xs or not ys:
        return None  # invalid frame, don't trust this reading

    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)

    return HandPosition(x=cx, y=cy)


def detect_movement_direction(
    prev: HandPosition,
    current: HandPosition,
    threshold: float = 0.12
) -> Tuple[bool, bool]:
    """
    Detect whether movement qualifies as a LEFT or UP swipe.

    FIXES:
    - Prevents tiny jitter from triggering swipes.
    - Clarified coordinate explanation.
    - Ensures stable gesture detection.
    """
    dx = current.x - prev.x
    dy = current.y - prev.y

    # LEFT: x decreases significantly
    # UP: y decreases significantly (image origin = top-left)
    is_left = dx < -threshold
    is_up = dy < -threshold

    return is_left, is_up


def is_hand_raised(current: HandPosition, height_threshold: float = 0.35) -> bool:
    """
    Simple heuristic: hand is 'raised' if its center is above a vertical threshold.

    FIXES:
    - Normalized coordinate interpretation clarified.
    - Ensures HandPosition is valid before comparing.
    """
    if current is None:
        return False

    # y < threshold means hand is closer to top of frame
    return current.y < height_threshold
