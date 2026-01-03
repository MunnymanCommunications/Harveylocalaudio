#!/bin/bash
cd "$(dirname "$0")/desktop-app"
source venv/bin/activate
python app.py
