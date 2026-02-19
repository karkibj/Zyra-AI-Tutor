"""
LangGraph RAG Service - No database dependencies
Works without chat history persistence
"""
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.agents.workflow import get_tutor_workflow
from app.agents.state import AgentState, ConversationMessage


class LangGraphRAGService:
    """RAG service using LangGraph - stateless (no DB chat history)"""
    
    def __init__(self):
        self.workflow = get_tutor_workflow()
        self.sessions = {}  # In-memory session storage
    
    async def ask(
        self,
        question: str,
        chapter_filter: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Ask a question using LangGraph multi-agent workflow
        NO DATABASE CHAT HISTORY (for now)
        """
        start_time = datetime.now()
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get conversation history from memory
        if not conversation_history and session_id in self.sessions:
            conversation_history = self.sessions[session_id]
        
        # Prepare conversation history for state
        history_messages = []
        if conversation_history:
            for msg in conversation_history[-10:]:
                history_messages.append(
                    ConversationMessage(
                        role=msg.get('role', 'user'),
                        content=msg.get('content', ''),
                        timestamp=datetime.now()
                    )
                )
        
        # Create initial state
        initial_state = AgentState(
            question=question,
            user_id="anonymous",
            session_id=session_id,
            chapter_filter=chapter_filter,
            conversation_history=history_messages
        )
        
        # Run through LangGraph workflow
        final_state = self.workflow.invoke(initial_state)
        
        # Handle both dict and object returns from LangGraph
        if isinstance(final_state, dict):
            # LangGraph returned a dict
            final_answer = final_state.get('final_answer', '')
            intent = final_state.get('intent', 'unknown')
            sources = final_state.get('sources', [])
            retrieved_contexts = final_state.get('retrieved_contexts', [])
            examples = final_state.get('examples', [])
            practice_questions = final_state.get('practice_questions', [])
            agent_path = final_state.get('agent_path', [])
            curriculum_check = final_state.get('curriculum_check', {})
        else:
            # LangGraph returned AgentState object
            final_answer = getattr(final_state, 'final_answer', '') or ''
            intent = getattr(final_state, 'intent', 'unknown') or 'unknown'
            sources = getattr(final_state, 'sources', [])
            retrieved_contexts = getattr(final_state, 'retrieved_contexts', [])
            examples = getattr(final_state, 'examples', [])
            practice_questions = getattr(final_state, 'practice_questions', [])
            agent_path = getattr(final_state, 'agent_path', [])
            curriculum_check = getattr(final_state, 'curriculum_check', {})
        
        # Store conversation in memory
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append({
            'role': 'user',
            'content': question
        })
        
        if final_answer:
            self.sessions[session_id].append({
                'role': 'assistant',
                'content': final_answer
            })
        
        # Keep only last 20 messages per session
        if len(self.sessions[session_id]) > 20:
            self.sessions[session_id] = self.sessions[session_id][-20:]
        
        # Calculate response time
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        # Build response
        return {
            "answer": final_answer or "I encountered an error processing your question.",
            "intent": intent,
            "sources": sources,
            "session_id": session_id,
            "chunk_count": len(retrieved_contexts),
            "response_time": elapsed_time,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "agent_path": agent_path,
                "curriculum_check": curriculum_check,
                "examples_provided": len(examples),
                "practice_offered": len(practice_questions) > 0
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        from app.services.vector_store_service import get_vector_store
        
        vector_store = get_vector_store()
        vector_stats = vector_store.get_stats()
        
        return {
            "workflow": "langgraph_multi_agent",
            "vector_store": vector_stats,
            "embedding_model": "all-MiniLM-L6-v2",
            "llm_model": "gemini-2.5-flash",
            "agents": [
                "intent_router",
                "retriever", 
                "curriculum_agent",
                "tutor_agent",
                "example_agent",
                "practice_suggester",
                "response_compiler"
            ],
            "active_sessions": len(self.sessions)
        }


# Global instance 
_langgraph_rag_service = None

def get_langgraph_rag_service() -> LangGraphRAGService:
    """Get global LangGraph RAG service instance"""
    global _langgraph_rag_service
    if _langgraph_rag_service is None:
        _langgraph_rag_service = LangGraphRAGService()
    return _langgraph_rag_service