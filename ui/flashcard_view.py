from typing import List, Dict, Any, Optional


class FlashcardView:
    """
    Represents flashcard UI state.
    Now also carries optional STT/evaluation metadata.
    """

    def to_dict(
        self,
        current_english: Optional[str],
        current_spanish: Optional[str],
        learned: List[str],
        study_more: List[str],
        revisit: List[str],
        recognized_text: Optional[str] = None,
        evaluation: Optional[bool] = None,
    ) -> Dict[str, Any]:

        data = {
            "current_card": {
                "english": current_english,
                "spanish": current_spanish,
            },
            "learned_words": learned,
            "study_more_words": study_more,
            "revisit_words": revisit,
        }

        if recognized_text is not None:
            data["recognized_text"] = recognized_text

        if evaluation is not None:
            data["evaluation"] = evaluation

        return data
