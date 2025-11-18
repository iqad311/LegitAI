# backend/gemini_client.py

import google.generativeai as genai
from pydantic import BaseModel
from typing import Optional
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

# Configure API key
genai.configure(api_key=GEMINI_API_KEY)


# Pydantic structured response
class AiasLLMResponse(BaseModel):
    requested_level: int
    is_within_selected_level: bool
    violation_reason: Optional[str]
    assistant_reply_md: str


def call_aias_model(prompt: str) -> AiasLLMResponse:
    """
    Calls Gemini using structured JSON output.
    Works on Streamlit Cloud.
    """

    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config={
            "response_mime_type": "application/json",
        },
        response_schema=AiasLLMResponse,
    )

    response = model.generate_content(prompt)

    # Gemini returns python object automatically
    return response
