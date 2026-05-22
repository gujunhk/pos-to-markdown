@echo off
if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Please run setup.cmd first.
    exit /b 1
)
call .venv\Scripts\activate.bat
python main.py