# Gesture-Controlled English → Spanish Flashcard App

A small but complete **gesture-controlled + speech-to-text language-learning prototype**.

- 👋 Control the app with **hand gestures** (via camera).
- 🧠 Practice **English → Spanish vocabulary**.
- 🎙 Use a **pluggable STT layer** (dummy-mode by default).
- 💻 Python backend (FastAPI) + React/Tailwind front-end (Christmas themed).
- 🧪 Includes dev + test scripts and simple self-tests.

---

## 1. What This Project Does

This application demonstrates a realistic **take-home assignment** for:

- Fast prototyping.
- Shipping a coherent end-to-end feature.
- Practical use of **computer vision** (gesture detection with MediaPipe).
- Simple, reliable (pluggable) **speech-to-text** logic.
- Clean, modular architecture.
- Thoughtful documentation and a clear expansion roadmap.

**Core Experience:**

1. The system shows an **English word** from a fixed vocabulary.
2. The user raises their hand in front of the camera to indicate they want to answer.
3. The backend **prompts for the Spanish translation** (dummy STT).
4. The answer is evaluated:
   - ✅ Correct → card moves to `learned_words`.
   - ❌ Incorrect → card moves to `revisit_words`.
5. The user can gesture:
   - **Swipe Up** → mark as `study_more_words` (keep practicing).
   - **Swipe Left** → skip for now and revisit later.

The React front-end displays the **current card and deck breakdown** in a Christmas-themed UI, while the OpenCV window handles the computer-vision gesture view.

---

## 2. How to Run It

### 2.1 Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- A webcam
- (Optional) A terminal that supports ANSI colors for CLI feedback.

### 2.2 Backend Setup (Python)

```bash
cd language_learning_gesture_app

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Run the backend:

```bash
python main.py
```

or directly with Uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

This will:

- Start the FastAPI backend on `http://localhost:8000`.
- Open an OpenCV window titled **"Gesture Camera"**.
- Start reading webcam frames and detecting gestures.

### 2.3 Frontend Setup (React + TailwindCSS)

```bash
cd language_learning_gesture_app/frontend

npm install
npm run dev
```

Open the logged URL (typically `http://localhost:5173`) in your browser.

### 2.4 One-Command Dev Script

From the project root:

```bash
./dev.sh
```

This will:

- Start the Python backend on port 8000.
- Start the React dev server on port 5173.

> Stop with `Ctrl+C` in the terminal. The script will attempt to kill the backend process.

### 2.5 Run Tests

From the project root:

```bash
./test.sh
```

Which runs:

```bash
python self_test.py
```

to validate the most important core logic.

---

## 3. File Structure

```text
language_learning_gesture_app/
│── main.py
│── requirements.txt
│── README.md
│── DailyLog.md
│── dev.sh
│── test.sh
│── self_test.py
│── word_bank.py
│
├── cv/
│   ├── gesture_detector.py
│   ├── hand_utils.py
│   └── __init__.py
│
├── stt/
│   ├── speech_to_text.py
│   └── __init__.py
│
├── ui/
│   ├── flashcard_view.py
│   ├── animations.py
│   └── __init__.py
│
└── frontend/
    ├── package.json
    ├── index.html
    ├── vite.config.js
    ├── postcss.config.js
    ├── tailwind.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── styles/
        │   └── globals.css
        └── components/
            ├── Flashcard.jsx
            ├── ChristmasFrame.jsx
            └── GestureIcons.jsx
```

---

## 4. File-by-File Responsibilities & Key Functions

### 4.1 `main.py`

**Responsibility:** Core application orchestration.

- Defines `DeckManager`
  - Maintains the word list and current index.
  - Tracks `learned_words`, `study_more_words`, and `revisit_words`.
  - `evaluate_spoken(spoken: str) -> bool`:
    - Normalizes and compares the provided Spanish text to the expected translation.
    - On correct: moves card to `learned_words`.
    - On incorrect: moves card to `revisit_words`.
  - `get_state()`:
    - Returns a serializable dictionary via `FlashcardView`.

- Defines `ConnectionManager`
  - Manages WebSocket clients (`connect`, `disconnect`).
  - `broadcast_state(state)`:
    - Sends updated deck state to all connected clients.
  - `broadcast_event(event)`:
    - Sends gesture/evaluation events to all connected clients.

- FastAPI app:
  - `GET /api/state` → returns current deck state.
  - `WebSocket /ws` → handles real-time updates.

- Startup event:
  - Captures the running asyncio loop.
  - Starts `GestureDetector` on a background thread.

- `handle_gesture(event: GestureEvent)`:
  - Handles `SWIPE_LEFT`, `SWIPE_UP`, `HAND_UP`.
  - On `HAND_UP`, invokes `SpeechToText.transcribe()`.
  - Uses `Animations` for CLI feedback.
  - Broadcasts updated state and events via WebSockets.

### 4.2 `word_bank.py`

- Defines `WORD_BANK`, a simple **English → Spanish** map:

```python
WORD_BANK = {
    "dog": "perro",
    "cat": "gato",
    "house": "casa",
    "car": "coche",
    "water": "agua",
    "food": "comida",
    "school": "escuela",
    "friend": "amigo",
    "love": "amor",
    "sun": "sol",
}
```

### 4.3 `cv/hand_utils.py`

Helpers for gesture detection.

- `HandPosition`:
  - Dataclass storing `x`, `y` in normalized coordinates (0–1).

- `compute_hand_center(landmarks, image_width, image_height) -> HandPosition | None`:
  - Computes average landmark position as an approximate “hand center”.

- `detect_movement_direction(prev, current, threshold=0.12) -> (is_left, is_up)`:
  - Compares `current` vs `prev` center to detect left/up movement beyond a threshold.

- `is_hand_raised(current, height_threshold=0.35) -> bool`:
  - Heuristic: if `current.y < height_threshold`, treat as “hand raised”.

### 4.4 `cv/gesture_detector.py`

**Responsibility:** Real-time gesture detection from webcam.

- `GestureEvent`:
  - Dataclass containing `type` and `timestamp`.

- `GestureDetector`:
  - Uses `mediapipe.solutions.hands.Hands`.
  - In `run()`:
    - Grabs frames from camera via `cv2.VideoCapture`.
    - Computes hand center via `compute_hand_center`.
    - Uses `detect_movement_direction` for swipe detection.
      - `SWIPE_LEFT` when Δx < -threshold.
      - `SWIPE_UP` when Δy < -threshold.
    - Uses `is_hand_raised` + time threshold for `HAND_UP` detection.
    - For each detected gesture, calls the provided `callback(GestureEvent)`.
    - Shows an OpenCV preview window.

### 4.5 `stt/speech_to_text.py`

**Responsibility:** Abstract speech-to-text interface.

- `SpeechToText(mode="dummy", api_key=None)`:
  - `mode="dummy"` → no external dependencies.
  - `transcribe()`:
    - In dummy mode: prints prompt and returns user-typed text.
    - Ready for expansion to real STT using Whisper/OpenAI.

### 4.6 `ui/flashcard_view.py`

**Responsibility:** Deck state representation for any front-end.

- `FlashcardView.to_dict(...)`:
  - Accepts:
    - `current_english`
    - `current_spanish`
    - `learned`
    - `study_more`
    - `revisit`
  - Returns a dict of the form:

```python
{
  "current_card": {"english": "...", "spanish": "..."},
  "learned_words": [...],
  "study_more_words": [...],
  "revisit_words": [...],
}
```

### 4.7 `ui/animations.py`

**Responsibility:** Terminal-based “animations”.

- `show_correct_animation()`:
  - Prints a green `✔ Correct!` message.

- `show_incorrect_animation()`:
  - Prints a red `✘ Incorrect.` message.

UI clients (like React) can use the same semantics to trigger their own visual animations.

### 4.8 `self_test.py`

**Responsibility:** Lightweight sanity tests for core logic.

- `test_word_bank()`:
  - Asserts basic mappings (e.g., `"dog" -> "perro"`).

- `test_hand_utils()`:
  - Asserts that a clear left movement and raised hand are detected correctly.

- `test_flashcard_view()`:
  - Asserts the dictionary structure produced by `FlashcardView`.

- `run_all()`:
  - Runs all tests and prints success.

### 4.9 Scripts

- `dev.sh`:
  - Starts backend (Uvicorn) and front-end (Vite) in dev mode.

- `test.sh`:
  - Calls `python self_test.py`.

### 4.10 Frontend Files (React + Tailwind)

#### `frontend/package.json`

Defines dependencies:

- `react`, `react-dom`
- `vite`
- `tailwindcss`, `postcss`, `autoprefixer`
- `framer-motion` (lightweight animation library)

#### `frontend/src/main.jsx`

- Bootstraps React with `App` into `#root`.

#### `frontend/src/App.jsx`

- Maintains state:

  - `currentCard`
  - `learned`, `studyMore`, `revisit`
  - `lastEvent` (e.g., evaluation result)

- On mount:

  - Fetches initial state from `GET /api/state`.
  - Opens WebSocket to `ws://localhost:8000/ws`.
  - Updates UI when `state` or `event` messages are received.

- Renders:

  - `ChristmasFrame` → decorative border.
  - `Flashcard` → central card.
  - `GestureIcons` → legend for gestures.

#### `frontend/src/components/Flashcard.jsx`

- Displays the current English word.
- Shows counts for each deck category.
- Highlights the last evaluation as green/red using `framer-motion` for fade + scale animations.

#### `frontend/src/components/ChristmasFrame.jsx`

- Wraps children in a Christmas-themed frame:

  - Background: gradient using black, red, and green.
  - Border with small icon row (🎄, 🎁, ❄️, 🔔).
  - Soft glow and hover animation.

#### `frontend/src/components/GestureIcons.jsx`

- Shows gesture legend:

  - 👋 Hand Up → answer.
  - ⬆️ Swipe Up → study more.
  - ⬅️ Swipe Left → revisit later.

#### `frontend/src/styles/globals.css`

- Tailwind base + custom tweaks for holiday theme.

---

## 5. Gesture Definitions & Meanings

### 5.1 Swipe Left

- **Detection:** Hand center moves significantly left between frames.
  - `dx < -threshold` with `threshold ≈ 0.12` (normalized).
- **Meaning:** “Skip this card for now, revisit later.”
- **Deck Update:** Adds current word to `revisit_words` and advances to the next card.

### 5.2 Swipe Up

- **Detection:** Hand center moves significantly upward between frames.
  - `dy < -threshold` with `threshold ≈ 0.12` (normalized).
- **Meaning:** “Mark this as something I want to study more.”
- **Deck Update:** Adds current word to `study_more_words` and advances to the next card.

### 5.3 Hand Up (Static)

- **Detection:** Hand is above a vertical threshold for at least 200ms.
  - `current.y < 0.35` for ≥ 0.2 seconds.
- **Meaning:** “I want to answer this card.”
- **Action:**
  - Triggers STT (dummy mode: typed response).
  - Evaluates the response.
  - Shows correct/incorrect feedback.
  - Moves card to `learned_words` or `revisit_words` and advances.

---

## 6. Speech-to-Text Logic

### 6.1 Dummy Mode (Implemented)

The default STT mode is **dummy** to keep the project completely self-contained.

- When `HAND_UP` is detected:
  - Backend prints:
    - `[STT] HAND_UP detected. Please type the Spanish translation you would say:`
  - User types the Spanish word in the terminal.
  - Text is normalized (trimmed, lowercased).
  - Compared against the expected Spanish translation from `WORD_BANK`.

### 6.2 Real STT (Future Hook)

To use a real STT backend (e.g., Whisper):

1. Extend `SpeechToText`:
   - Add `mode="openai"`.
   - Record audio (using PyAudio or sounddevice).
   - Upload to an STT service (OpenAI Whisper API, whisper.cpp, etc.).

2. Modify `transcribe()`:
   - In `"openai"` mode, record from the microphone, send audio, and return text.

This design isolates all STT work in a single file so the rest of the app is unaffected.

---

## 7. Vocabulary Deck Logic

Three categories:

1. **learned_words**
   - Words answered correctly via STT evaluation.

2. **study_more_words**
   - Words explicitly marked by swiping up.

3. **revisit_words**
   - Words skipped by swiping left **or** answered incorrectly.

The flow:

1. Start with `WORD_BANK` as a simple list of `(english, spanish)` pairs.
2. `DeckManager` tracks the current index.
3. When an action occurs:
   - **SWIPE_LEFT** → add to `revisit_words`, then advance.
   - **SWIPE_UP** → add to `study_more_words`, then advance.
   - **HAND_UP** → STT evaluation:
     - If correct → add to `learned_words`, then advance.
     - If incorrect → add to `revisit_words`, then advance.

The deck loops in a **circular** fashion; this keeps the prototype simple while demonstrating lifecycle transitions.

---

## 8. Model Assumptions, Limitations & Design Decisions

### 8.1 Assumptions

- Single user with a single webcam.
- Moderate lighting and clear hand gestures.
- User is comfortable typing in dummy STT mode for now.
- Vocabulary is small and static for demonstration purposes.

### 8.2 Limitations

- Gesture detection is **heuristic-based**, not ML-trained:
  - Large, slow gestures work best.
  - False positives may appear with rapid movement.

- STT is dummy-only out of the box:
  - No actual audio recording or streaming is performed.
  - All “speech” is simulated via keyboard input.

- Exact string match for evaluation:
  - No handling for accents, synonyms, or minor typos.
  - No fuzzy matching or edit distance.

- No persistence layer:
  - Deck state is in-memory only; restarting the backend resets progress.

### 8.3 Design Decisions

- **Python + MediaPipe** for fast prototyping of gestures.
- **FastAPI + WebSockets**:
  - Clear, modern REST + real-time communication model.
  - Easy integration with React front-end.
- **Dummy STT abstraction**:
  - Keeps the demo fully runnable on any machine.
  - Clean seam to plug in real STT when desired.
- **React + Tailwind front-end**:
  - Simple, yet production-leaning front-end stack.
  - Christmas theme to show basic design/branding capability.

---

## 9. Future Expansion Roadmap (10+ Ideas)

This project is intentionally small but has a wide growth surface.

1. **Real STT Integration**
   - Implement Whisper API or whisper.cpp backend.
   - Add configurable language/locale settings.

2. **Spaced Repetition System (SRS)**
   - Use Leitner boxes or SM-2 algorithm.
   - Schedule `revisit_words` intelligently over time.

3. **Confidence Scoring**
   - Allow users to rate their confidence (e.g., 1–5) after each answer.
   - Bias scheduling based on self-reported confidence.

4. **Partial Matching & Fuzzy Scoring**
   - Use Levenshtein distance / token-based similarity.
   - Accept minor spelling errors.
   - Provide hints (e.g., “almost correct, missing accent”).

5. **Multi-Language Support**
   - Support more language pairs (English ↔ French, English ↔ Portuguese, etc.).
   - Use a pluggable vocabulary loader from JSON or CSV.

6. **User Profiles & Persistence**
   - Store progress per user in a local DB (SQLite) or cloud backend.
   - Add sign-in and per-user decks, streaks and stats.

7. **Leaderboards & Gamification**
   - Track XP, streaks, and accuracy.
   - Display global or local leaderboards.
   - Unlock badges for milestones (e.g., “100 words learned”).

8. **Adaptive Gesture Models**
   - Fine-tune thresholds based on user-specific movement patterns.
   - Add more gestures (e.g., swipe right to “I know this perfectly”).

9. **AR / MR Mode**
   - Overlay flashcards on top of camera feed using AR libraries.
   - Allow pointing to objects in the environment to learn vocabulary.

10. **Grammar & Sentence Mode**
    - Move beyond single-word vocab.
    - Prompt full sentences and check grammatical structures.

11. **Offline-First Mode**
    - Bundle a local STT engine (whisper.cpp).
    - Cache decks and progress for offline usage.

12. **Mobile Port**
    - Rebuild front-end with React Native or Expo.
    - Use mobile camera for gestures and built-in microphone for STT.

13. **Teacher Dashboard**
    - Allow educators to define custom decks.
    - Track classroom-wide performance and usage patterns.

14. **Analytics & Insights**
    - Aggregate per-word difficulty stats.
    - Identify “problem” words and surface them more frequently.

---

## 10. How to Extend This for a Real Take-Home

If this were a real interview take-home, possible extensions you could mention:

- Hook up real STT (Whisper) and discuss trade-offs.
- Improve gesture robustness with smoothing / debouncing.
- Add a small persistence layer and user profiles.
- Write more extensive automated tests (pytest, mock gesture events).
- Ship a minimal Dockerfile for easy evaluation.

---

If you want, we can next:

- Swap dummy STT for a real Whisper integration.
- Add fuzzy matching for Spanish answers.
- Improve the React UI with more detailed stats and animations.
