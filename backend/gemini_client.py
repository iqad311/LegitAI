# backend/gemini_client.py

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel
import os
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

if GEMINI_API_KEY is None:
    raise RuntimeError("❌ GEMINI_API_KEY not found in environment variables!")

# Configure API
genai.configure(api_key=GEMINI_API_KEY)


# Pydantic response schema
class AiasLLMResponse(BaseModel):
    requested_level: int
    is_within_selected_level: bool
    violation_reason: Optional[str] = None
    assistant_reply_md: str


# Initialize Gemini Client
client = genai.configure(api_key=GEMINI_API_KEY)


# Public function: call_aias_model()
def call_aias_model(prompt: str) -> AiasLLMResponse:

    model = genai.GenerativeModel("gemini-2.0-flash")

    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )

    raw = response.text.strip()

    # Try direct JSON
    try:
        data = json.loads(raw)
        return AiasLLMResponse(**data)
    except Exception:
        pass

    # Try fallback: extract JSON manually
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        cleaned = raw[start:end]
        data = json.loads(cleaned)
        return AiasLLMResponse(**data)
    except Exception:
        pass

    # Final fallback — avoid backend crash
    return AiasLLMResponse(
        requested_level=1,
        is_within_selected_level=False,
        violation_reason="Model returned invalid JSON.",
        assistant_reply_md="⚠️ Internal parsing error — but I'm still here! Please try again."
    )






