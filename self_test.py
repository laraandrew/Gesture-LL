"""Lightweight sanity checks for core modules.

Run via: python self_test.py
"""
from word_bank import WORD_BANK
from ui.flashcard_view import FlashcardView
from stt.speech_to_text import SpeechToText
from cv.hand_utils import HandPosition, detect_movement_direction, is_hand_raised


def test_word_bank():
    assert "dog" in WORD_BANK and WORD_BANK["dog"] == "perro"


def test_hand_utils():
    prev = HandPosition(x=0.8, y=0.5)
    curr = HandPosition(x=0.5, y=0.5)
    left, up = detect_movement_direction(prev, curr, threshold=0.1)
    assert left and not up
    raised = is_hand_raised(HandPosition(x=0.5, y=0.2))
    assert raised


def test_flashcard_view():
    view = FlashcardView()
    state = view.to_dict("dog", "perro", ["dog"], [], [])
    assert state["current_card"]["english"] == "dog"


def run_all():
    print("Running self tests...")
    test_word_bank()
    test_hand_utils()
    test_flashcard_view()
    print("All self tests passed.")


if __name__ == "__main__":
    run_all()
