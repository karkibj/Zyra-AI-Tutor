import os
from typing import List, Dict

import requests
import streamlit as st
from dotenv import load_dotenv

# -----------------------
# 1. Config
# -----------------------

load_dotenv()

# You can override this in .env if backend runs elsewhere
API_BASE_URL = os.getenv("ZYRA_API_URL", "http://localhost:8000/api/v1")

def ask_tutor_backend(query: str, chapter: str = "money_exchange") -> str:
    """Call FastAPI backend /tutor/ask endpoint."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/tutor/ask",
            json={"query": query, "chapter": chapter},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("reply", "No reply field returned from backend.")
    except Exception as e:
        return f"Sorry, backend error: {e}"


# -----------------------
# 2. Streamlit UI
# -----------------------

st.set_page_config(
    page_title="Zyra – NEB Grade 10 Math Tutor",
    page_icon="",
    layout="centered",
)

st.title("🧮 Zyra – NEB Grade 10 Mathematics Tutor")
st.caption("FYP Demo – FastAPI + LangChain RAG (Money Exchange)")

# Chat history type
Message = Dict[str, str]

if "chat_history" not in st.session_state:
    st.session_state.chat_history: List[Message] = [
        {
            "role": "assistant",
            "content": (
                "Hi! I'm **Zyra**, your NEB Grade 10 Mathematics tutor. "
                "Ask me anything about the *Money Exchange* chapter, "
                "and I’ll explain it step by step using your syllabus notes."
            ),
        }
    ]

# Show existing messages
for msg in st.session_state.chat_history:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.markdown(msg["content"])

# Input from student
user_input = st.chat_input("Type your maths question here (Money Exchange)...")

if user_input:
    # Add user message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Ask backend
    with st.chat_message("assistant"):
        with st.spinner("Zyra (backend) is thinking..."):
            reply = ask_tutor_backend(user_input, chapter="money_exchange")

        st.markdown(reply)
        st.session_state.chat_history.append(
            {"role": "assistant", "content": reply}
        )

st.markdown(
    """
    <hr/>
    <small>Backend: FastAPI `/api/v1/tutor/ask` using LangChain + Gemini + RAG on Money Exchange notes.</small>
    """,
    unsafe_allow_html=True,
)
