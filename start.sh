#!/usr/bin/env bash
# Solar Documents Generator - start script (Linux / macOS)
set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate

pip install --quiet -r requirements.txt

echo ""
echo "Starting Solar Documents Generator..."
echo "Open http://localhost:5000 in your browser."
echo ""
python3 server.py
