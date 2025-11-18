# backend/gemini_client.py
import os   
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel

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
client = genai.Client(api_key=GEMINI_API_KEY)


# Public function: call_aias_model()
def call_aias_model(prompt: str) -> AiasLLMResponse:
    """
    Calls Gemini with strict structured response (AiasLLMResponse).
    No streaming. Safe, stable.
    """

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.25,
                max_output_tokens=1200,
                response_mime_type="application/json",
                response_schema=AiasLLMResponse,  # <-- MAGIC: Gemini returns parsed
            ),
        )

        # Access structured object
        if hasattr(response, "parsed") and response.parsed:
            return response.parsed

        # Fallback: model did not respect schema
        return AiasLLMResponse(
            requested_level=0,
            is_within_selected_level=True,
            violation_reason="Model did not return structured JSON.",
            assistant_reply_md=response.text if hasattr(response, "text") else "",
        )

    except Exception as e:
        # Hard fallback for debugging
        return AiasLLMResponse(
            requested_level=0,
            is_within_selected_level=True,
            violation_reason=f"Backend exception: {e}",
            assistant_reply_md="Sorry — backend error occurred.",
        )




