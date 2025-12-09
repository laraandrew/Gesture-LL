from typing import List, Dict, Any, Optional


class FlashcardView:
    """Represents the flashcard state that can be rendered in any UI layer."""

    def to_dict(
        self,
        current_english: Optional[str],
        current_spanish: Optional[str],
        learned: List[str],
        study_more: List[str],
        revisit: List[str],
    ) -> Dict[str, Any]:
        return {
            "current_card": {
                "english": current_english,
                "spanish": current_spanish,
            },
            "learned_words": learned,
            "study_more_words": study_more,
            "revisit_words": revisit,
        }
