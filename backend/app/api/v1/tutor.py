# app/api/v1/tutor.py

from fastapi import APIRouter
from pydantic import BaseModel
from app.rag.money_exchange import answer_money_exchange_query

router = APIRouter(prefix="/tutor", tags=["AI Tutor"])


# ---------------------------
# Request Body Model
# ---------------------------
class TutorQuery(BaseModel):
    query: str
    chapter: str = "money_exchange"   


# ---------------------------
# Tutor Route
# ---------------------------
@router.post("/ask")
async def ask_tutor(payload: TutorQuery):
    """
    Main endpoint for student → Zyra tutor communication.
    """
    user_query = payload.query
    chapter = payload.chapter.lower()

    # For now, only Money Exchange is implemented
    if chapter == "money_exchange":
        response = answer_money_exchange_query(user_query)
    else:
        response = f"Sorry, the chapter '{chapter}' is not available yet."

    return {"reply": response}
