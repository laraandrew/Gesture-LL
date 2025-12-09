#!/usr/bin/env bash
set -e

echo "[test] Running Python self tests"
python self_test.py

echo "[test] (Optional) You can also run frontend tests, e.g. npm test, from ./frontend"
