from typing import Dict, Optional, List
from app.rag.pipeline import ZyraTutorPipeline


class TutorService:
    """Service layer for tutor operations."""
    
    def __init__(self):
        self.pipeline = ZyraTutorPipeline()
    
    def ask_question(
        self,
        query: str,
        chapter: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Process a student's question.
        
        Args:
            query: Student's question
            chapter: Optional chapter context
            conversation_history: Previous conversation
            
        Returns:
            Response dictionary
        """
        return self.pipeline.process_query(
            query=query,
            chapter=chapter,
            conversation_history=conversation_history
        )

# Global instance
tutor_service = TutorService()