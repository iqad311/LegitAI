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
    Streamlit-safe Gemini call.
    Handles:
    - schema output
    - safety fallbacks
    - Streamlit limitations
    """

    try:
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.2,
                "max_output_tokens": 4096,
            },
            safety_settings={
                "HARASSMENT": "BLOCK_NONE",
                "HATE_SPEECH": "BLOCK_NONE",
                "SEXUAL": "BLOCK_NONE",
                "DANGEROUS_CONTENT": "BLOCK_NONE",
            },
            response_schema=AiasLLMResponse,
        )

        response = model.generate_content(prompt)

        # Gemini sometimes returns wrong object shape
        if isinstance(response, AiasLLMResponse):
            return response

        # If Gemini returns dict-like structure
        if hasattr(response, "text") and response.text:
            try:
                return AiasLLMResponse.model_validate_json(response.text)
            except Exception:
                pass

        raise ValueError("Malformed Gemini structured output")

    except Exception as e:
        import traceback
        print("\n\n===== BACKEND CRASH REPORT =====")
        traceback.print_exc()
        print("================================\n\n")
        
        err = f"⚠️ Backend crashed: {type(e).__name__}"
        with st.chat_message("assistant"):
            st.markdown(err)
    
        messages.append({"role": "assistant", "content": err})
        st.stop()

