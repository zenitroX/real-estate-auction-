@echo off
title SKANDX Backend API Server
echo ========================================================
echo Starting SKANDX Backend REST API Server (Port 8000)...
echo ========================================================

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" serve.py
) else (
    python serve.py
)
pause
