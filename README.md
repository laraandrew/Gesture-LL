## Images

<img width="683" height="730" alt="Screenshot 2025-12-09 at 6 56 59 PM" src="https://github.com/user-attachments/assets/b9b156d3-51ed-47c7-bdb2-88bcab8e7cd1" />
<img width="663" height="734" alt="Screenshot 2025-12-09 at 6 57 48 PM" src="https://github.com/user-attachments/assets/4577ce8e-7f8c-463b-a5e7-447b0a611484" />
<img width="643" height="757" alt="Screenshot 2025-12-09 at 6 58 44 PM" src="https://github.com/user-attachments/assets/ba6ef012-2fad-4a82-ad56-f60ed71eb137" />


# Gesture-LL

Gesture-LL is a gesture-driven, speech-aware language-learning prototype built to explore how computer vision and voice can shape a responsive study loop. The project pairs real-time hand tracking with speech-to-text to keep the interface lightweight while still feeling alive.

## User Experience
- The camera watches for simple gestures to drive the session: raise a hand to answer, swipe up to mark “study more,” swipe left to skip and revisit later.
- When a hand raise is detected, the backend prompts for the Spanish translation of the current English word and evaluates the response.
- A React front end mirrors state from the backend over WebSockets, showing the current card plus counts for learned, study-more, and revisit decks.
- The OpenCV preview gives immediate visual feedback for gesture detection while the browser UI handles the study flow.

## System Overview
- **FastAPI + Async:** The backend is an async FastAPI app so gesture ingestion, speech prompts, and WebSocket pushes can run concurrently without blocking.
- **Gesture Pipeline:** MediaPipe runs on a background thread to stream frames from OpenCV, detect hand centers, and emit gestures (swipe left, swipe up, hand raise) with timestamps.
- **Speech-to-Text (Whisper-ready):** A thin `SpeechToText` abstraction keeps dummy text input for local development but is structured to swap in Whisper or another STT provider without touching the rest of the app.
- **WebSockets + State Management:** A `ConnectionManager` broadcasts deck state and gesture/evaluation events to any connected client. State is held in memory by `DeckManager`, which tracks the active card and the learned/study-more/revisit buckets.
- **Front End:** A small React + Tailwind client consumes the state feed, renders the flashcard view, and highlights recent events. The design is intentionally minimal so the focus stays on the interaction model.

## Gesture Design
- **Hand Raise:** Detected when the hand sits above a vertical threshold for a short dwell time. Triggers STT and evaluation for the current card.
- **Swipe Up:** Upward delta beyond a movement threshold. Marks the card for additional practice and advances the deck.
- **Swipe Left:** Leftward delta beyond a movement threshold. Skips the card for now and adds it to the revisit list.

These gestures were chosen for low cognitive load and to keep the camera-facing interaction obvious and debounced against noise.

## Speech-to-Text Abstraction
- The `SpeechToText` class exposes a single `transcribe()` method. In dummy mode it collects typed input; in a production mode it would record audio and call Whisper or another STT engine.
- Evaluation is string-based today to keep the demo deterministic. The surrounding logic is isolated so fuzzy matching or accent-aware comparison can drop in later.

## Architecture Highlights
- **Deck Manager:** Owns card rotation and categorization, returning serializable state for any UI. The deck loops to keep the session continuous without persistence.
- **Connection Manager:** Manages WebSocket clients and pushes both state snapshots and discrete events, giving the UI immediate feedback after each gesture or evaluation.
- **Background Gesture Thread:** Keeps computer vision work off the event loop while still invoking async handlers for downstream effects.
- **REST + WebSockets:** `GET /api/state` seeds clients; `/ws` streams updates so the browser stays in sync without polling.

## Design Decisions and Trade-offs
- **Heuristic gestures over ML:** MediaPipe landmarks plus thresholds ship quickly and are transparent to debug. Trade-off: sensitivity to lighting and motion; may need smoothing for production.
- **Dummy STT by default:** Guarantees the project runs anywhere without cloud keys. Trade-off: no true audio loop until Whisper (or similar) is wired in.
- **In-memory state:** Simplicity beats persistence for a prototype. Trade-off: progress resets on restart; multi-user support would require a store.
- **Separate CV and UI loops:** OpenCV preview stays snappy while the browser UI renders state. Trade-off: two surfaces to consider for UX consistency.

## Roadmap
- **Whisper-backed STT:** Stream microphone audio, add latency handling, and surface transcription confidence in the UI.
- **Gesture smoothing and calibration:** Per-user thresholds, motion averaging, and better debounce to cut false positives.
- **Persistence and profiles:** Store deck progress per user (SQLite/Postgres) and keep history for spaced repetition scheduling.
- **Richer evaluation:** Fuzzy matching, accent handling, and partial-credit scoring for near-miss answers.
- **Content model:** Load decks from JSON/CSV, support multiple language pairs, and tag words for adaptive difficulty.
- **Deployment track:** Package backend and front end behind a single entry point (container or Procfile) with env-configured STT providers.

## Getting Started
The repository includes `dev.sh` to boot both FastAPI and the Vite dev server together, plus `test.sh` for the core sanity checks. Python, Node, and a webcam are the only hard requirements; swap the STT mode when you are ready to plug in Whisper.
