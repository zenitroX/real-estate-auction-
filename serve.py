"""
Root API Server Entrypoint.
Delegates to backend/app.py for clean separated hosting.
"""
import sys
from pathlib import Path

# Add backend directory to path and run
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

from app import main

if __name__ == "__main__":
    main()
