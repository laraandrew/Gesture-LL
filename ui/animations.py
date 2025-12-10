class Animations:
    """
    Handles feedback animations for correct/incorrect answers.
    Also emits events that the WebSocket can forward to the frontend.
    """

    def __init__(self, ws_manager=None):
        self.ws_manager = ws_manager  # injected from main.py

    def show_correct_animation(self):
        """Show correct answer animation (synchronous for terminal output)."""
        print("\033[92m✔ Correct! Great job!\033[0m")  # Green text

    def show_incorrect_animation(self):
        """Show incorrect answer animation (synchronous for terminal output)."""
        print("\033[91m✘ Incorrect. This card will be revisited.\033[0m")  # Red text
