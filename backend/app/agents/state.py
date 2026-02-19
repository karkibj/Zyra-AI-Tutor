"""
LangGraph State Definitions
State that flows through the agent workflow
"""
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ConversationMessage(BaseModel):
    """Single message in conversation"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class RetrievedContext(BaseModel):
    """Context retrieved from vector store"""
    text: str
    content_id: str
    title: str
    score: float
    chapter: Optional[str] = None


class AgentState(BaseModel):
    """
    State that flows through LangGraph workflow
    Each agent reads and updates this state
    """
    # Input
    question: str
    user_id: str
    session_id: Optional[str] = None
    chapter_filter: Optional[str] = None
    
    # Conversation context
    conversation_history: List[ConversationMessage] = Field(default_factory=list)
    
    # Intent classification
    intent: Optional[str] = None
    is_greeting: bool = False
    is_math_question: bool = False
    is_practice_request: bool = False
    
    # Retrieved context
    retrieved_contexts: List[RetrievedContext] = Field(default_factory=list)
    
    # Agent outputs
    curriculum_check: Optional[Dict] = None  # Prerequisites, related topics
    explanation: Optional[str] = None  # Main explanation
    examples: List[str] = Field(default_factory=list)  # Worked examples
    practice_questions: List[Dict] = Field(default_factory=list)  # Generated questions
    
    # Final output
    final_answer: Optional[str] = None
    sources: List[Dict] = Field(default_factory=list)
    
    # Metadata
    processing_time: float = 0.0
    agent_path: List[str] = Field(default_factory=list)  # Track which agents ran
    
    class Config:
        arbitrary_types_allowed = True