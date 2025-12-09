#!/usr/bin/env bash
set -e

# ----------------------------
# PROJECT ROOT RESOLUTION
# ----------------------------
# Resolve script directory → repo root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
VENV_DIR="$PROJECT_ROOT/.venv"

echo "[dev] Project root: $PROJECT_ROOT"

# ----------------------------
# PYTHON ENVIRONMENT SETUP
# ----------------------------
if [ ! -d "$VENV_DIR" ]; then
  echo "[dev] Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

echo "[dev] Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "[dev] Installing backend requirements..."
pip install --upgrade pip
pip install -r "$PROJECT_ROOT/requirements.txt"

# ----------------------------
# START PYTHON BACKEND
# ----------------------------
echo "[dev] Starting Python backend on http://localhost:8000"
$VENV_DIR/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# function to clean up backend if user exits script
cleanup() {
    echo ""
    echo "[dev] Cleaning up backend (PID $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    echo "[dev] Shutdown complete."
}
trap cleanup EXIT

# ----------------------------
# FRONTEND SETUP & START
# ----------------------------
echo "[dev] Entering frontend directory..."
cd "$FRONTEND_DIR"

echo "[dev] Installing frontend dependencies (npm install)..."
npm install

echo "[dev] Starting React front-end on http://localhost:5173"
echo "[dev] Press Ctrl+C to stop."
npm run dev
