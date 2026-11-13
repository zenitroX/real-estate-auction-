@echo off
title Bank Auction Web Portal
echo ========================================================
echo Starting High-Speed Bank Auction Web Server...
echo ========================================================

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" serve.py
) else (
    python serve.py
)
pause
