from typing import List, Dict, Optional
from app.rag.intent_classifier import IntentClassifier, Intent
from app.rag.retriever import DocumentRetriever
from app.rag.generator import ResponseGenerator


class ZyraTutorPipeline:
    """Main RAG pipeline orchestrating intent classification, retrieval, and generation."""
    
    def __init__(self, data_dir: str = "data/chapters"):
        self.intent_classifier = IntentClassifier()
        self.retriever = DocumentRetriever(data_dir)
        self.generator = ResponseGenerator()
        
        # Initialize vectorstore
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """Initialize or load vectorstore."""
        # Try to load existing vectorstore
        if not self.retriever.load_vectorstore():
            # Create new vectorstore if not found
            print("Creating new vectorstore...")
            self.retriever.create_vectorstore()
            self.retriever.save_vectorstore()
    
    def process_query(
        self, 
        query: str, 
        chapter: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, any]:
        """
        Process a user query through the complete pipeline.
        
        Args:
            query: User's question
            chapter: Optional chapter context
            conversation_history: Previous messages
            
        Returns:
            Dict with response and metadata
        """
        # Classify intent
        intent = self.intent_classifier.classify(query)
        
        print(f"Detected intent: {intent}")
        
        # Route based on intent
        if intent == Intent.MATHEMATICAL_QUERY:
            # Use RAG for mathematical queries
            return self._handle_mathematical_query(query, chapter)
        
        elif intent in [Intent.GREETING, Intent.FEEDBACK, Intent.CLARIFICATION]:
            # Use conversational response (no RAG needed)
            return self._handle_conversational(query, conversation_history)
        
        elif intent == Intent.OFF_TOPIC:
            # Politely redirect to math
            return self._handle_off_topic(query)
        
        else:
            # Default to RAG
            return self._handle_mathematical_query(query, chapter)
    
    def _handle_mathematical_query(self, query: str, chapter: Optional[str]) -> Dict:
        """Handle mathematical queries using RAG."""
        try:
            # Retrieve relevant documents
            docs = self.retriever.retrieve(query, k=4)
            
            # Generate response
            response = self.generator.generate_rag_response(query, docs)
            
            return {
                "reply": response,
                "intent": Intent.MATHEMATICAL_QUERY.value,
                "sources": [
                    {
                        "chapter": doc.metadata.get("chapter", "unknown"),
                        "content_preview": doc.page_content[:100] + "..."
                    }
                    for doc in docs
                ],
                "used_rag": True
            }
        except Exception as e:
            print(f"Error in RAG pipeline: {e}")
            return {
                "reply": "I'm having trouble accessing my study materials right now. Could you rephrase your question?",
                "intent": Intent.MATHEMATICAL_QUERY.value,
                "error": str(e),
                "used_rag": False
            }
    
    def _handle_conversational(
        self, 
        message: str, 
        history: Optional[List[Dict]]
    ) -> Dict:
        """Handle greetings, feedback, clarifications without RAG."""
        response = self.generator.generate_conversational_response(message, history)
        
        return {
            "reply": response,
            "intent": "CONVERSATIONAL",
            "used_rag": False
        }
    
    def _handle_off_topic(self, query: str) -> Dict:
        """Handle off-topic queries."""
        response = (
            "That's an interesting question, but I'm specifically here to help you with "
            "Grade 10 Mathematics for your SEE preparation!  "
            "Is there any math topic you'd like to learn about? "
            "I can help with Sets, Algebra, Geometry, Trigonometry, Statistics, and more!"
        )
        
        return {
            "reply": response,
            "intent": Intent.OFF_TOPIC.value,
            "used_rag": False
        }
    
    def add_chapter_materials(self, chapter: str):
        """Add new chapter materials to vectorstore."""
        print(f"Adding materials for chapter: {chapter}")
        docs = self.retriever.load_documents(chapter)
        chunks = self.retriever.text_splitter.split_documents(docs)
        
        if self.retriever.vectorstore:
            self.retriever.vectorstore.add_documents(chunks)
            self.retriever.save_vectorstore()
            print(f"Added {len(chunks)} chunks for {chapter}")