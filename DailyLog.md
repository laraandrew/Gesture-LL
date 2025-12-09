# Daily Development Log – Gesture-Controlled Language Learning App

## 1. Project Framing & Goals
- Clarified the target use case: gesture-controlled English → Spanish flashcard trainer.
- Captured core success criteria:
  - Fast prototyping and clear feature shipping.
  - Practical computer vision using MediaPipe + OpenCV.
  - Simple, pluggable speech-to-text (STT) with a dummy fallback.
  - Clean architecture with clear module boundaries.
  - A small but complete end-to-end experience.

## 2. Architecture & File Layout
- Locked in the required Python backend structure:

  - `main.py`: FastAPI app, WebSocket hub, and orchestration.
  - `word_bank.py`: shared vocabulary dictionary.
  - `cv/`: gesture detection, hand utilities.
  - `stt/`: speech-to-text abstraction.
  - `ui/`: view/state representations and simple terminal animations.

- Added additional helpful files:
  - `dev.sh`: convenience script to run backend and frontend together.
  - `test.sh`: script to run backend sanity tests.
  - `self_test.py`: simple test harness to validate core logic.

- Decided to run:
  - Backend on `http://localhost:8000` (FastAPI + WebSockets).
  - Front-end on `http://localhost:5173` (Vite + React + Tailwind).

## 3. Backend Core Implementation

### 3.1 Deck Manager & State Representation
- Implemented `DeckManager` in `main.py` to:
  - Maintain the current card index.
  - Track `learned_words`, `study_more_words`, and `revisit_words`.
  - Advance through the deck in a circular fashion.
  - Evaluate spoken (or typed) answers against `WORD_BANK` (exact match).

- Implemented `FlashcardView` in `ui/flashcard_view.py` to:
  - Convert internal deck state into a serializable dictionary for UI layers.
  - Provide a clear contract between backend logic and any front-end renderer.

### 3.2 Gesture Detection
- Implemented `GestureDetector` in `cv/gesture_detector.py`:
  - Uses MediaPipe Hands to detect landmarks.
  - Computes a simple hand “center” using `compute_hand_center` from `hand_utils.py`.
  - Evaluates delta movement between frames to detect:
    - `SWIPE_LEFT` when the hand moves left beyond a threshold.
    - `SWIPE_UP` when the hand moves up beyond a threshold.
  - Detects `HAND_UP` when the hand remains above a vertical threshold for > 200ms.
  - Draws landmarks and helper text onto an OpenCV window.
  - Emits `GestureEvent` objects through a callback.

- Implemented helpers in `cv/hand_utils.py`:
  - `HandPosition` dataclass for clarity.
  - `detect_movement_direction` for up/left heuristics.
  - `is_hand_raised` to approximate “hand raised” using normalized y-coordinate.

### 3.3 Speech-to-Text (STT) Abstraction
- Implemented `SpeechToText` in `stt/speech_to_text.py`:
  - Default mode: `dummy`, which prompts the user for typed input.
  - Future-ready for extension to real STT providers (Whisper/OpenAI, etc.).
  - Keeps the project self-contained and fully runnable without extra setup.

### 3.4 Animations & Feedback
- Implemented `Animations` in `ui/animations.py`:
  - Termininal-based feedback using ANSI colors.
  - `show_correct_animation()` (green checkmark).
  - `show_incorrect_animation()` (red cross).
  - Mirrors the same semantic events the React front-end can animate visually.

### 3.5 FastAPI & WebSocket Integration
- Implemented FastAPI app in `main.py`:
  - `GET /api/state`: returns the full deck state for HTTP clients.
  - `WebSocket /ws`: pushes state & event updates to React clients.
  - `ConnectionManager`:
    - Tracks active WebSocket connections.
    - Broadcasts both `state` and `event` messages.

- Startup event:
  - Captures the main asyncio loop in `ASYNC_LOOP`.
  - Starts `GestureDetector` in a background thread.
  - The gesture callback uses `asyncio.run_coroutine_threadsafe` to:
    - Broadcast deck state and evaluation events back to WebSocket clients.

### 3.6 Evaluation Flow
- `handle_gesture` in `main.py` wires everything together:
  - `SWIPE_LEFT` → marks current card as `revisit_words`, advances deck.
  - `SWIPE_UP` → marks current card as `study_more_words`, advances deck.
  - `HAND_UP` → triggers STT:
    - In dummy mode: prompt user to type the Spanish translation.
    - Evaluate typed answer against `WORD_BANK[current_word]`.
    - Correct → `learned_words`, green animation.
    - Incorrect → `revisit_words`, red animation.
  - Broadcasts the updated state & evaluation result over WebSocket.

## 4. Front-End (React + Tailwind, Christmas Theme)

### 4.1 Design Decisions
- Kept the front-end minimal and focused:
  - Single-page dashboard showing:
    - Current English word.
    - Learned / Study More / Revisit counts.
    - Last evaluation result (correct/incorrect).
  - Connects via WebSocket for near-real-time updates.
  - Fetches initial state via `GET /api/state`.

- Theming:
  - Christmas palette: black, white, red, green.
  - Small festive icon row (emoji-based) around the flashcard.
  - Subtle hover & entrance animations using a lightweight animation library.

### 4.2 React Implementation Steps
- Initialized a Vite React project.
- Set up TailwindCSS + PostCSS.
- Created `Flashcard` component to show current word state.
- Created `ChristmasFrame` to wrap content in a holiday border.
- WebSocket logic:
  - On mount:
    - Fetch initial state from the backend.
    - Connect to `ws://localhost:8000/ws`.
    - Update React state on `state` or `event` messages.
  - Animate green/red feedback on correct/incorrect evaluations.

## 5. Scripts & Testing

### 5.1 dev.sh
- Starts backend with Uvicorn on port 8000.
- Starts frontend development server on port 5173.
- Cleans up backend process when the front-end exits.

### 5.2 test.sh & self_test.py
- `test.sh` runs `python self_test.py`.
- `self_test.py` performs:
  - Sanity check on `WORD_BANK` contents.
  - Validates `hand_utils` movement & raise logic.
  - Validates `FlashcardView.to_dict` structure.

## 6. Model Assumptions & Limitations (High Level)
- STT is currently text-based (dummy mode) to keep the project self-contained.
- Gesture detection uses simple heuristics and may be noisy in real environments.
- Single-user, single-camera scenario is assumed.
- Deck is small and in-memory; persistence is not yet implemented.
- Exact string match is required for correctness (no fuzziness or diacritics handling).

## 7. Final Checks & Packaging
- Verified that:
  - Backend starts successfully with `uvicorn main:app`.
  - `self_test.py` passes all checks.
  - Front-end compiles with Vite/Tailwind.
- Prepared project layout for zipping and distribution.
