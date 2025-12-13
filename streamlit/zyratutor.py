# zyratutor.py  (LangChain-based Zyra tutor)

import os
from typing import List, Dict

import streamlit as st
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# -----------------------
# 1. Setup & configuration
# -----------------------

load_dotenv()  
API_KEY = "AIzaSyAL99koPqlBMtPkS5b4MN13vZHhpbHPWgU"

if not API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY not found. Please set it in a .env file or environment variable."
    )

MODEL_NAME = "gemini-2.5-flash"  
# Tutor persona prompt
TUTOR_PERSONA = """
You are Zyra, a friendly, patient AI Tutor for NEB / SEE Grade 10 Mathematics.

Your goals:
- Explain concepts in very simple, clear English.
- Break solutions into short, numbered steps where helpful.
- Gently ask clarifying questions if the student's query is vague.
- Encourage the student: be positive, supportive, and non-judgmental.

Rules:
- Focus on Grade 10 Mathematics topics (Money Exchange, Algebra, Geometry, etc.).
- If the question is completely outside the syllabus, say it politely and redirect to math.
- Do not just give final answers; explain how and why.
- Keep responses concise but clear (not more than about 8–10 sentences unless steps are needed).
"""


def format_history(history: List[Dict[str, str]]) -> str:
    """
    Convert chat history into a simple text conversation for the model.
    """
    convo = []
    for msg in history:
        speaker = "Student" if msg["role"] == "user" else "Zyra"
        convo.append(f"{speaker}: {msg['content']}")
    return "\n".join(convo)


# ---- LangChain pieces ----

# 1) LLM
llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    google_api_key=API_KEY,
    temperature=0.3,
)

# 2) Prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", TUTOR_PERSONA),
        (
            "human",
            """Here is the conversation so far between you (Zyra) and the student:

{history}

Now the student asks: "{user_message}"

Respond as Zyra, following the rules above.
Use simple English and, when needed, explain in short, numbered steps.""",
        ),
    ]
)

# 3) Output parser → convert model result to plain string
parser = StrOutputParser()

# 4) Chain: history + user_message → prompt → LLM → string
tutor_chain = prompt | llm | parser


def generate_reply(history: List[Dict[str, str]], user_message: str) -> str:
    """
    Call the LangChain tutor_chain with history + latest question.
    """
    history_text = format_history(history)
    return tutor_chain.invoke({"history": history_text, "user_message": user_message})


# -----------------------
# 2. Streamlit UI
# -----------------------

st.set_page_config(
    page_title="Zyra – NEB Grade 10 Math Tutor",
    page_icon="🧮",
    layout="centered",
)

st.title(" Zyra – NEB Grade 10 Mathematics Tutor")


# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history: List[Dict[str, str]] = [ 
        {
            "role": "assistant",
            "content": (
                "Hi! I'm **Zyra**, your NEB Grade 10 Mathematics tutor. "
                "Ask me anything related to your maths syllabus, and I'll help step by step."
            ),
        }
    ]

# Display existing messages
for msg in st.session_state.chat_history:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Type your maths question here...")

if user_input:
    # 1) Show user message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2) Generate tutor reply via LangChain
    with st.chat_message("assistant"):
        with st.spinner("Zyra is thinking..."):
            try:
                reply = generate_reply(st.session_state.chat_history, user_input)
            except Exception as e:
                reply = f"Sorry, I ran into an error: `{e}`"

            st.markdown(reply)
            st.session_state.chat_history.append(
                {"role": "assistant", "content": reply}
            )
