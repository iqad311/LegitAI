# backend/engine.py

from __future__ import annotations

from enum import IntEnum
from typing import List, Dict, Any

from backend.gemini_client import call_aias_model, AiasLLMResponse



# AIAS LEVEL ENUM

class AiasLevel(IntEnum):
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5


def _level_from_int(value: int) -> AiasLevel:
    try:
        return AiasLevel(value)
    except ValueError:
        return AiasLevel.LEVEL_2  # fallback default


# PROMPT BUILDING LOGIC

INTENT_RULES = """
INTENT HANDLING RULES (MANDATORY, DO NOT BREAK):

You MUST detect the user's intent **before generating your response**.

1. EXPLANATION MODE
   If the user says:
   - "explain", "describe", "what does this do",
   - "how does this work", "walk me through",
   - "explain the code", "explain this output"
   → This is EXPLANATION.
   → You MUST NOT generate new code.
   → ONLY explain the content provided in conversation.

2. FIX / DEBUG / IMPROVE MODE
   Words like:
   - "fix", "debug", "improve", "refactor", "make this better"
   → Improve ONLY the student’s provided content.
   → Do NOT generate a fresh full solution unless AIAS ≥ 4.

3. CODE GENERATION MODE
   Words like:
   - "write", "generate", "make", "create", "build", "code"
   → Allowed ONLY if AIAS Level ≥ 4.
   → If user asks for code but level < 4 → violation.

4. IF INTENT IS UNCLEAR
   → Default to EXPLANATION instead of code.
   → Never assume the user wanted code unless clearly stated.

**CRITICAL RULE**
If the user requests an EXPLANATION, you MUST NOT regenerate full code under ANY level.
"""


def build_aias_prompt(selected_level: AiasLevel,
                      user_message: str,
                      history: List[Dict[str, str]]) -> str:
    """
    Build prompt ensuring:
    - AIAS rules
    - Intent classification
    - Level restriction
    - Structured output from model
    """

    # Build short conversation history
    history_lines: List[str] = []
    for msg in history[-6:]:   # last six messages
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_lines.append(f"{role.upper()}: {content}")

    history_block = ""
    if history_lines:
        history_block = "Conversation so far:\n" + "\n".join(history_lines) + "\n\n"


    # LEVEL RULES

    LEVEL_RULES = f"""
        AIAS LEVEL RULES (STRICT):

        LEVEL 1 — No AI Assistance
        - NOT allowed: academic explanations, examples, concepts, summaries,
        writing help, programming, code, assignment content.
        - ALLOWED: study habits, motivation, productivity, wellbeing,
        AIAS rule explanations ONLY.

        LEVEL 2 — Limited Assistance
        - High-level conceptual help ONLY.
        - Allowed: brainstorming, outlines.
        - NOT allowed: detailed solutions, full paragraphs, code.

        LEVEL 3 — Moderate Assistance
        - Can improve or debug student-provided work.
        - NOT allowed: generating full new solutions.

        LEVEL 4 — Significant Assistance
        - Full examples, code, solutions allowed.
        - Must still stay within academic integrity boundaries.

        LEVEL 5 — AI-Dominant Assistance
        - Fully unrestricted academic support.
        """

    # FINAL PROMPT

    prompt = f"""
        You are **LegitAI**, an Integrity-Safe AI Assistant.

        Follow ALL rules exactly.

        {LEVEL_RULES}

        {INTENT_RULES}

        Your job:
        1. Read the student's selected AIAS level: {selected_level.value}
        2. Determine your own "actual assistance level" (1–5).
        3. Decide if your reply violates the selected level.
        4. Output JSON fields ONLY:
        - requested_level: integer 1–5
        - is_within_selected_level: true/false
        - violation_reason: null or short string
        - assistant_reply_md: markdown response

        {history_block}

        Student’s latest message:
        \"\"\"{user_message}\"\"\"
        """

    return prompt


# OVERRIDE: Prevent code regeneration during explanations

def apply_explanation_override(user_message: str) -> str:
    """
    If user clearly asks for explanation, ensure model NEVER generates new code.
    """
    lowered = user_message.lower()

    explanation_triggers = [
        "explain", "explanation",
        "describe", "walk me through",
        "what does this do",
        "how does this work",
        "explain the code"
    ]

    if any(word in lowered for word in explanation_triggers):
        return user_message + (
            "\n\nIMPORTANT: The user is explicitly asking for an explanation. "
            "Do NOT generate new code. ONLY explain the existing code."
        )

    return user_message


# MODEL RESPONSE PROCESSING

def generate_aias_response(selected_level_int: int,
                           user_message: str,
                           history: List[Dict[str, str]]) -> AiasLLMResponse:
    """
    Build prompt → call Gemini → validate → return structured.
    """

    selected_level = _level_from_int(selected_level_int)

    # Apply explanation override
    safe_user_message = apply_explanation_override(user_message)

    prompt = build_aias_prompt(selected_level, safe_user_message, history)

    llm_resp = call_aias_model(prompt)

    # Safety clamp
    if llm_resp.requested_level not in (1, 2, 3, 4, 5):
        llm_resp.requested_level = selected_level.value

    allowed = llm_resp.requested_level <= selected_level.value

    if llm_resp.is_within_selected_level != allowed:
        llm_resp.is_within_selected_level = allowed

        if not allowed and not llm_resp.violation_reason:
            llm_resp.violation_reason = f"This exceeds AIAS Level {selected_level.value}."

    return llm_resp


# PUBLIC API FOR FRONTEND

def chat_with_aias(selected_level_int: int,
                   user_message: str,
                   history: List[Dict[str, str]]) -> Dict[str, Any]:

    llm_resp = generate_aias_response(selected_level_int, user_message, history)

    return {
        "requested_level": llm_resp.requested_level,
        "is_within_selected_level": llm_resp.is_within_selected_level,
        "violation_reason": llm_resp.violation_reason,
        "assistant_reply": llm_resp.assistant_reply_md,
    }
