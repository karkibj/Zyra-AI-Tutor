from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from app.core.llm import get_llm
from app.core.prompts import (
    TUTOR_SYSTEM_PROMPT,
    RAG_CONTEXT_PROMPT,
    CONVERSATIONAL_PROMPT
)


class ResponseGenerator:
    """Generates responses using LLM with or without RAG context."""
    
    def __init__(self):
        self.llm = get_llm(temperature=0.3)
    
    def generate_rag_response(
        self, 
        query: str, 
        context_docs: List[Document]
    ) -> str:
        """
        Generate response using RAG (context from retrieved documents).
        
        Args:
            query: User's question
            context_docs: Retrieved relevant documents
            
        Returns:
            Generated response
        """
        # Format context from documents
        context_text = "\n\n".join([
            f"[From {doc.metadata.get('chapter', 'curriculum')}]:\n{doc.page_content}"
            for doc in context_docs
        ])
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", TUTOR_SYSTEM_PROMPT),
            ("human", RAG_CONTEXT_PROMPT)
        ])
        
        # Create chain
        chain = prompt | self.llm | StrOutputParser()
        
        # Generate response
        response = chain.invoke({
            "context": context_text,
            "question": query
        })
        
        return response
    
    def generate_conversational_response(
        self, 
        message: str, 
        history: List[dict] = None
    ) -> str:
        """
        Generate conversational response (no RAG needed).
        
        Args:
            message: User's message
            history: Conversation history
            
        Returns:
            Generated response
        """
        # Format history
        history_text = ""
        if history:
            for msg in history[-5:]:  # Last 5 messages for context
                role = "Student" if msg["role"] == "user" else "Zyra"
                history_text += f"{role}: {msg['content']}\n"
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", TUTOR_SYSTEM_PROMPT),
            ("human", CONVERSATIONAL_PROMPT)
        ])
        
        # Create chain
        chain = prompt | self.llm | StrOutputParser()
        
        # Generate response
        response = chain.invoke({
            "history": history_text,
            "message": message
        })
        
        return response