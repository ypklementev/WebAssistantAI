#!/bin/bash

set -e  # выходим при любом ошибочном коде

echo "🔌 Activating virtual environment..."
if [ ! -d "venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

echo "🧩 Installing Chromium for Playwright..."
playwright install chromium

echo "🤖 Starting agent..."
python3 src/main.py