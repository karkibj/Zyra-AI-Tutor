# app/rag/money_exchange.py

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

# Global singletons
_vectorstore = None
_llm = None

# -----------------------------
# 1. Tutor persona prompt
# -----------------------------
SYSTEM_PROMPT = """
You are Zyra — a friendly, patient SEE / NEB Grade 10 Mathematics AI Tutor.

Your goals:
- Explain concepts in very simple, clear English.
- Break solutions into short, numbered steps when needed.
- Use examples from the Grade 10 Mathematics syllabus, especially the Money Exchange chapter.
- Encourage the student and never be rude or judgmental.

Rules:
- Use the provided context (chapter notes) as your main source.
- If the notes do not clearly contain the answer, say:
  "I'm not fully sure, but here's what I can help you understand…"
- Never invent formulas. Always rely on correct mathematics.
"""


# -----------------------------
# 2. Build FAISS vectorstore once
# -----------------------------
def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        # 1) Load the Money Exchange notes from docx
        loader = Docx2txtLoader(
            "A:/Zyra-AI-Tutor/backend/data/chapters/money_exchange.docx"
        )
        docs = loader.load()

        # 2) Split into smaller chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=100,
        )
        chunks = splitter.split_documents(docs)

        # 3) Local embeddings (no Google API)
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # 4) Build FAISS index
        _vectorstore = FAISS.from_documents(chunks, embeddings)

    return _vectorstore


def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3,
        )
    return _llm


# -----------------------------
# 3. Main RAG function
# -----------------------------
def answer_money_exchange_query(user_query: str) -> str:
    """
    Used by FastAPI /tutor/ask.
    - Finds similar chunks from Money Exchange notes via FAISS.
    - Builds a plain-text prompt.
    - Sends prompt to Gemini and returns its answer.
    """
    try:
        vectorstore = get_vectorstore()

        # Retrieve top-k relevant chunks directly from FAISS
        docs = vectorstore.similarity_search(user_query, k=4)

        context_text = "\n\n".join(d.page_content for d in docs)

        prompt_text = f"""{SYSTEM_PROMPT}

Context from Money Exchange chapter notes:
{context_text}

Student question: {user_query}

Now answer as Zyra. Use:
- Simple English
- Step-by-step explanation where helpful
- If you do a calculation, show the working.
"""

        llm = get_llm()
        response = llm.invoke(prompt_text)

        return response.content

    except Exception as e:
        return f"Sorry, I encountered an error: {e}"""
