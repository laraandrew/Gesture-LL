from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class HandPosition:
    x: float
    y: float


def compute_hand_center(landmarks, image_width: int, image_height: int) -> Optional[HandPosition]:
    """Compute the approximate hand center in normalized screen coordinates (0-1).

    This uses the average of all landmark points, which is sufficient for simple
    swipe detection heuristics.
    """
    if not landmarks:
        return None
    xs = [lm.x for lm in landmarks]
    ys = [lm.y for lm in landmarks]
    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)
    return HandPosition(x=cx, y=cy)


def detect_movement_direction(prev: HandPosition, current: HandPosition, threshold: float = 0.12) -> Tuple[bool, bool]:
    """Detect whether movement between frames qualifies as left or up swipe.

    Returns (is_left, is_up).
    """
    dx = current.x - prev.x
    dy = current.y - prev.y

    # Negative dx = moved left, negative dy = moved up (image coordinates).
    is_left = dx < -threshold
    is_up = dy < -threshold
    return is_left, is_up


def is_hand_raised(current: HandPosition, height_threshold: float = 0.35) -> bool:
    """Determine if the hand is "raised" above a simple vertical threshold.

    We use a fraction of the image height instead of true body pose.
    """
    return current.y < height_threshold
