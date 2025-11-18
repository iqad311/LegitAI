# backend/config.py

import os
from dotenv import load_dotenv

# Ensure .env is loaded (GEMINI_API_KEY, GEMINI_MODEL, etc.)
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Please add it to your .env file."
    )

# Default model
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
