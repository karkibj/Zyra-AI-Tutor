import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/api/v1/tutor/ask"  

st.set_page_config(page_title="Zyra AI Tutor", layout="wide")
st.title("🧠 Zyra — SEE Grade 10 AI Math Tutor")

st.write("Ask anything from *Money Exchange* chapter.")

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for role, text in st.session_state.messages:
    if role == "user":
        st.chat_message("user").markdown(text)
    else:
        st.chat_message("assistant").markdown(text)   # ← FIXED

# Chat input
user_query = st.chat_input("Ask your math question...")

if user_query:
    # Add user message
    st.session_state.messages.append(("user", user_query))
    st.chat_message("user").markdown(user_query)

    # Send request to FastAPI backend
    payload = {
        "query": user_query,
        "chapter": "money_exchange"
    }

    try:
        response = requests.post(API_URL, json=payload)
        tutor_reply = response.json()["reply"]
    except Exception as e:
        tutor_reply = f"Error contacting server: {e}"

    # Add assistant message
    st.session_state.messages.append(("assistant", tutor_reply))
    st.chat_message("assistant").markdown(tutor_reply)   # ← FIXED
