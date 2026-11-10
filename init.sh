#!/bin/bash
set -euo pipefail

echo "Installing the all-live-stream checker..."
python -m pip install -r requirements.txt
echo "Source: playlists/ULTIMATE_LIVE_5261.m3u"
echo "Run: python src/main.py"
echo "Optional: set the BD_PROXY environment variable before running."
