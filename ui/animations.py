class Animations:
    """Simple text-based feedback for correct/incorrect answers.

    The React front-end can use its own richer animations.
    """

    def show_correct_animation(self):
        print("\033[92m✔ Correct! Great job!\033[0m")  # Green text

    def show_incorrect_animation(self):
        print("\033[91m✘ Incorrect. This card will be revisited.\033[0m")  # Red text
