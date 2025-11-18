# backend/gemini_client.py

import google.generativeai as genai
from pydantic import BaseModel
from typing import Optional
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

# Configure API key
genai.configure(api_key=GEMINI_API_KEY)

# Pydantic response model
class AiasLLMResponse(BaseModel):
    requested_level: int
    is_within_selected_level: bool
    violation_reason: Optional[str]
    assistant_reply_md: str

def call_aias_model(prompt: str) -> AiasLLMResponse:
    """
    Calls Gemini and parses JSON manually.
    Compatible with Streamlit Cloud (which uses older google-generativeai).
    """

    model = genai.GenerativeModel(GEMINI_MODEL)

    response = model.generate_content(
        prompt,
        generation_config={
            "response_mime_type": "application/json"
        }
    )

    # Gemini returns text → we must parse JSON manually.
    try:
        import json

        raw_text = response.text.strip()
        data = json.loads(raw_text)

        return AiasLLMResponse(**data)

    except Exception as e:
        print("\n\n===== JSON PARSE ERROR =====")
        print("Raw model output:\n", response.text)
        print("Error:", e)
        print("============================\n\n")

        # Return fallback safe object
        return AiasLLMResponse(
            requested_level=1,
            is_within_selected_level=False,
            violation_reason="Model returned invalid JSON.",
            assistant_reply_md="⚠️ Internal parsing error — but I'm still here! Please try again."
        )
