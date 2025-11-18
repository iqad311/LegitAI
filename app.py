import os
import time
import uuid
import math
import streamlit as st
from dotenv import load_dotenv
from backend.engine import chat_with_aias

# LOAD ENV VARIABLES
load_dotenv()


# PAGE CONFIG + CSS STYLES
st.set_page_config(page_title="LegitAI - AI assistance, at the right level.", page_icon="assets/icon.ico", layout="wide")

st.markdown("""
<style>
.center-title {
    text-align: center;
    margin-top: 25px;
    margin-bottom: 5px;
    font-size: 38px;
    font-weight: 700;
}
.center-intro {
    text-align: center;
    font-size: 17px;
    margin-top: -5px;
    margin-bottom: 30px;
    color: #cccccc;
}
.locked-box select {
    border: 3px solid #ff9800 !important;
    background-color: #fff3e0 !important;
    font-weight: 600 !important;
}
.sidebar-chat-btn {
    width: 100% !important;
    text-align: left !important;
}
</style>
""", unsafe_allow_html=True)


# SESSION STATE DEFAULTS

if "sessions" not in st.session_state:
    st.session_state.sessions = {}     # session_id → {"title": "", "messages": [], "level": None}

if "active_session" not in st.session_state:
    st.session_state.active_session = None

# Suggestions toggle (default ON)
if "enable_suggestions" not in st.session_state:
    st.session_state.enable_suggestions = True



# HELPERS

def parse_aias_level(choice: str):
    """Convert dropdown label into integer level."""
    if not choice.startswith("AIAS Level"):
        return None
    try:
        return int(choice.split()[2])
    except:
        return None


def get_active_chat():
    sid = st.session_state.active_session
    if sid and sid in st.session_state.sessions:
        return st.session_state.sessions[sid]
    return None


# CREATE DEFAULT FIRST SESSION (if none exists)

if not st.session_state.sessions:
    new_id = str(uuid.uuid4())
    st.session_state.sessions[new_id] = {
        "title": "New Chat",
        "messages": [],
        "level": None,
        "last_prompt": None,
        "last_message_count": 0,
        "last_suggestion_choice": None,
    }
    st.session_state.active_session = new_id


# SIDEBAR

with st.sidebar:
    st.image("assets/legitAI_logo.png")

    st.markdown("Use AI responsibly according to your **AI Assistance Scale (AIAS)**.")

    st.markdown("---")

    # NEW CHAT BUTTON
    if st.button("➕ New Chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.sessions[new_id] = {
            "title": "New Chat",
            "messages": [],
            "level": None,
            "last_prompt": None,
            "last_message_count": 0,
            "last_suggestion_choice": None,
        }
        st.session_state.active_session = new_id

        # RESET AIAS DROPDOWN
        if "aias_level_box" in st.session_state:
            st.session_state["aias_level_box"] = "Choose AIAS Level"

        st.rerun()


    st.markdown("---")
    st.header("💬 Conversations")

    badge_colors = {
        1: "gray",
        2: "blue",
        3: "green",
        4: "orange",
        5: "red",
    }

    for sid, session in st.session_state.sessions.items():
        lvl = session.get("level")
        raw_title = session.get("title", "New Chat")


        # FIXED-HEIGHT TRUNCATION

        max_chars = 28
        title = raw_title[:max_chars] + ("…" if len(raw_title) > max_chars else "")


        # ROW LAYOUT (equal heights)

        col_title, col_badge = st.columns([7, 1])

        # LEFT: TITLE BUTTON
        with col_title:
            clicked = st.button(
                title,
                key=f"session_{sid}",
                use_container_width=True,
                help=raw_title  # full title on hover
            )

        # RIGHT: LEVEL BADGE
        with col_badge:
            color = badge_colors.get(lvl, "#9e9e9e")
            badge_label = f"L{lvl}" if lvl else "–"

            st.markdown(
                f"""
                <div style="
                    background-color:{color};
                    color:white;
                    text-align:center;
                    border-radius:6px;
                    padding:6px 0;
                    height:38px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-size:12px;
                    font-weight:600;">
                    {badge_label}
                </div>
                """,
                unsafe_allow_html=True,
            )

        if clicked:
            st.session_state.active_session = sid
            st.rerun()


    st.markdown("---")
    st.header("Settings")

    # Auto-suggestions toggle
    st.session_state.enable_suggestions = st.toggle(
        "💡 Enable Suggestions",
        value=st.session_state.enable_suggestions
    )

    st.toggle("🌙 Dark Mode (coming soon)")

    # Export chat transcript
    active = get_active_chat()
    if active:
        transcript = f"Chat Title: {active['title']}\n"
        transcript += f"AIAS Level: {active.get('level', 'Not selected')}\n"
        transcript += "-"*40 + "\n\n"

        for msg in active["messages"]:
            role = "USER" if msg["role"] == "user" else "ASSISTANT"
            transcript += f"{role}:\n{msg['content']}\n\n"

        st.download_button(
            "⬇️ Export This Chat (testing)",
            data=transcript,
            file_name=f"{active['title']}.txt",
            mime="text/plain",
            use_container_width=True
        )



# AIAS LEVEL DROPDOWN

active_chat = get_active_chat()
locked_level = active_chat["level"]

levels_list = [
    "Choose AIAS Level",
    "AIAS Level 1 – No AI Assistance",
    "AIAS Level 2 – Limited Assistance",
    "AIAS Level 3 – Moderate Assistance",
    "AIAS Level 4 – Significant Assistance",
    "AIAS Level 5 – AI-Dominant Exploration",
]

# Determine dropdown index
dropdown_index = 0
if locked_level:
    dropdown_index = locked_level
elif locked_level is None:
    saved_choice = st.session_state.get("aias_level_box")
    if saved_choice:
        parsed = parse_aias_level(saved_choice)
        if parsed:
            dropdown_index = parsed

disabled_flag = locked_level is not None

center_col = st.columns([4, 3, 4])[1]
with center_col:
    container_class = "locked-box" if disabled_flag else ""
    st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)

    level_choice = st.selectbox(
        "AIAS Level",
        levels_list,
        index=dropdown_index,
        key="aias_level_box",
        label_visibility="collapsed",
        disabled=disabled_flag,
    )

    st.markdown('</div>', unsafe_allow_html=True)

chosen_level = parse_aias_level(level_choice)


# CHAT TITLE + EMPTY CHAT

messages = active_chat["messages"]

if len(messages) == 0:
    st.markdown("<h1 class='center-title'>LegitAI</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='center-intro'>Welcome! Choose your AIAS level above and begin your first question.</p>",
        unsafe_allow_html=True,
    )

    with st.expander("ℹ️ What is AIAS?"):
        st.subheader("AI Assistance Scale (AIAS)")
        st.markdown("""Universities use AIAS to define how much AI usage is acceptable for each assignment. Your AIAS level determines how much help I’m allowed to give.""")
        st.subheader("Level Summary")
        st.markdown("""
            - **Level 1:** No AI assistance for assignment-specific help  
            - **Level 2:** Planning, outlining, concept help only  
            - **Level 3:** Help *with your draft* only  
            - **Level 4:** Significant AI-guided development  
            - **Level 5:** Full AI exploration & problem solving  
            """)
        url = "https://aiassessmentscale.com/"
        st.markdown(f"Learn more about AIAS [here]({url}).")

st.markdown("---")


# DISPLAY PAST MESSAGES
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# USER INPUT BAR
user_input = st.chat_input("Ask anything...")


# LEVEL-BASED SUGGESTION LIST
level = active_chat["level"] or chosen_level

if level == 1:
    suggestion_list = [
        "What is the AIAS scale?",
        "Give me study tips",
        "What counts as academic misconduct?",
        "How to plan my assignment?",
        "How to improve my focus?",
    ]
elif level == 2:
    suggestion_list = [
        "Explain recursion conceptually",
        "Give me a high-level outline",
        "Brainstorm essay ideas",
        "Summarize a topic briefly",
        "Explain gradient descent simply",
    ]
elif level == 3:
    suggestion_list = [
        "Improve my draft",
        "Rewrite this paragraph",
        "Debug this code snippet",
        "Suggest better structure",
        "Check clarity of my writing",
    ]
elif level == 4:
    suggestion_list = [
        "Give a worked recursion example",
        "Show a sample Python function",
        "Explain this algorithm step-by-step",
        "Break down this math problem",
        "Help refine a partially written solution",
    ]
elif level == 5:
    suggestion_list = [
        "Write a complete Python example program",
        "Explain this topic in full depth",
        "Generate a full solution from scratch",
        "Optimize this code or algorithm",
        "Solve this complex problem fully",
    ]
else:
    suggestion_list = [
        "What is the AIAS scale?",
        "Give me study tips",
        "What counts as academic misconduct?",
        "How to plan my assignment?",
        "How to improve my focus?",
    ]


# FIXED SUGGESTION HANDLING (NO MORE RE-TRIGGER)

suggestion_clicked = None

if user_input is None and st.session_state.enable_suggestions:
    with st.container():

        st.markdown("Suggestions")

        raw_choice = st.pills(
            label="Click a suggestion:",
            label_visibility="collapsed",
            options=suggestion_list,
            key=f"suggestions_bar_{st.session_state.active_session}",   # key per chat
        )

        prev_choice = active_chat.get("last_suggestion_choice")

        # Only treat as new click if it CHANGED
        if raw_choice and raw_choice != prev_choice:
            suggestion_clicked = raw_choice
            active_chat["last_suggestion_choice"] = raw_choice
        else:
            suggestion_clicked = None


# DETERMINE FINAL PROMPT

prompt = None

if user_input:
    prompt = user_input
elif suggestion_clicked:
    prompt = suggestion_clicked

# No user action → stop
if not prompt:
    st.stop()



# prevents export / dropdown / toggle rerun from re-sending last prompt

if "last_prompt" not in active_chat:
    active_chat["last_prompt"] = None
if "last_message_count" not in active_chat:
    active_chat["last_message_count"] = 0

current_msg_count = len(messages)

if prompt == active_chat["last_prompt"] and current_msg_count == active_chat["last_message_count"]:
    st.stop()


# SAVE USER MESSAGE

messages.append({"role": "user", "content": prompt})

with st.chat_message("user"):
    st.markdown(prompt)


# Rename chat title on first message
if active_chat["title"] == "New Chat":
    title_short = prompt[:40] + ("..." if len(prompt) > 40 else "")
    active_chat["title"] = title_short


# Lock level
if active_chat["level"] is None:
    active_chat["level"] = chosen_level


# Ensure level chosen
if active_chat["level"] is None:
    warn_text = (
        "⚠️ Please select an **AIAS Level** above first.\n\n"
        "I need to know what level of assistance is allowed."
    )
    with st.chat_message("assistant"):
        st.markdown(warn_text)
    messages.append({"role": "assistant", "content": warn_text})

    active_chat["last_prompt"] = prompt
    active_chat["last_message_count"] = len(messages)
    st.stop()


# CALL BACKEND

try:
    result = chat_with_aias(
        selected_level_int=active_chat["level"],
        user_message=prompt,
        history=messages,
    )
except Exception as e:
    print("[AIAS BACKEND ERROR]", repr(e))
    err_msg = "⚠️ Error contacting backend. Please try again."
    with st.chat_message("assistant"):
        st.markdown(err_msg)
    messages.append({"role": "assistant", "content": err_msg})

    active_chat["last_prompt"] = prompt
    active_chat["last_message_count"] = len(messages)
    st.stop()


assistant_text = result["assistant_reply"]
violation = result["violation_reason"]
is_ok = result["is_within_selected_level"]

if not is_ok and violation:
    assistant_text = f"⚠️ **AIAS Level Notice:** {violation}\n\n---\n\n" + assistant_text


# STREAMING OUTPUT

with st.chat_message("assistant"):
    placeholder = st.empty()
    streamed = ""

    for line in assistant_text.split("\n"):
        streamed += line + "\n"
        placeholder.markdown(streamed)
        time.sleep(0.03)

messages.append({"role": "assistant", "content": assistant_text})


# UPDATE RERUN GUARD VALUES

active_chat["last_prompt"] = prompt
active_chat["last_message_count"] = len(messages)

st.stop()
