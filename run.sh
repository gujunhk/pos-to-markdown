#!/bin/bash
if [ ! -f ".venv/bin/python" ]; then
    echo "Virtual environment not found. Please run setup.sh first."
    exit 1
fi
source .venv/bin/activate
python main.py