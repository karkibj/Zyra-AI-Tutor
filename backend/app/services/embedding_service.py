"""
Embedding Service
Generate vector embeddings for semantic search
"""
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
from pathlib import Path


class EmbeddingService:
    """Generate and manage embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding model
        
        Args:
            model_name: HuggingFace model name
            - "all-MiniLM-L6-v2" (384 dim, fast, good quality) ← DEFAULT
            - "all-mpnet-base-v2" (768 dim, slower, better quality)
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Lazy load the model"""
        if self.model is None:
            print(f"📥 Loading embedding model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            print(f"✅ Model loaded! Dimension: {self.model.get_sentence_embedding_dimension()}")
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings
            
        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])
        
        # Encode texts
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32,
            convert_to_numpy=True
        )
        
        return embeddings
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Single text string
            
        Returns:
            numpy array of shape (embedding_dim,)
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    @property
    def embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()


# Global instance (singleton pattern)
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """Get global embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service