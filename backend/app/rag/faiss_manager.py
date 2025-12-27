"""
FAISS Manager - Builds and queries vector index from database
"""
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
import faiss
import pickle
from pathlib import Path

from app.services.embedding_service import EmbeddingService
from app.core.config import settings


class FAISSManager:
    """Manages FAISS index for semantic search"""
    
    def __init__(self):
        self.index: Optional[faiss.IndexFlatL2] = None
        self.chunk_ids: List[uuid.UUID] = []
        self.dimension: int = 0
    
    async def build_index_from_database(
        self, 
        db: AsyncSession,
        document_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Build FAISS index from database embeddings
        
        Args:
            db: Database session
            document_id: If provided, build index only for this document
                        If None, build index for all documents
        
        Returns: Index statistics
        """
        # Get embeddings from database
        if document_id:
            embeddings = await EmbeddingService.get_embeddings_by_document(db, document_id)
        else:
            embeddings = await EmbeddingService.get_all_embeddings_for_search(db)
        
        if not embeddings:
            raise ValueError("No embeddings found in database")
        
        # Extract vectors and chunk IDs
        vectors = np.array([emb.embedding_vector for emb in embeddings], dtype=np.float32)
        self.chunk_ids = [emb.chunk_id for emb in embeddings]
        self.dimension = vectors.shape[1]
        
        # Create FAISS index
        print(f"🔨 Building FAISS index with {len(vectors)} vectors (dim={self.dimension})...")
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(vectors)
        
        return {
            "vectors_indexed": len(vectors),
            "dimension": self.dimension,
            "index_type": "IndexFlatL2"
        }
    
    def search(
        self,
        query_embedding: List[float],
        k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using query embedding
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            
        Returns: List of {chunk_id, score, rank}
        """
        if self.index is None:
            raise ValueError("Index not built. Call build_index_from_database() first")
        
        k = k or settings.RETRIEVAL_K
        k = min(k, len(self.chunk_ids))  # Don't request more than available
        
        # Convert query to numpy array
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # Search
        distances, indices = self.index.search(query_vector, k)
        
        # Format results
        results = []
        for rank, (idx, distance) in enumerate(zip(indices[0], distances[0])):
            if idx < len(self.chunk_ids):  # Valid index
                results.append({
                    "chunk_id": self.chunk_ids[idx],
                    "score": float(distance),
                    "rank": rank
                })
        
        return results
    
    async def search_and_retrieve(
        self,
        db: AsyncSession,
        query_embedding: List[float],
        k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search and retrieve full chunk content from database
        
        Returns: List of {chunk_id, content, score, rank, chunk_type}
        """
        from app.services.chunk_service import ChunkService
        
        # Search for similar chunks
        search_results = self.search(query_embedding, k)
        
        # Retrieve full chunks from database
        results = []
        for result in search_results:
            chunk = await ChunkService.get_chunk(db, result["chunk_id"])
            if chunk:
                results.append({
                    "chunk_id": str(chunk.chunk_id),
                    "content": chunk.content,
                    "score": result["score"],
                    "rank": result["rank"],
                    "chunk_type": chunk.chunk_type,
                    "token_count": chunk.token_count
                })
        
        return results
    
    def save_index(self, filepath: str = None):
        """Save FAISS index to disk"""
        if self.index is None:
            raise ValueError("No index to save")
        
        filepath = filepath or str(Path(settings.VECTORSTORE_PATH) / "faiss_index.bin")
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Save index
        faiss.write_index(self.index, filepath)
        
        # Save chunk IDs mapping
        mapping_file = filepath.replace(".bin", "_mapping.pkl")
        with open(mapping_file, "wb") as f:
            pickle.dump({
                "chunk_ids": self.chunk_ids,
                "dimension": self.dimension
            }, f)
        
        return {
            "index_file": filepath,
            "mapping_file": mapping_file
        }
    
    def load_index(self, filepath: str = None):
        """Load FAISS index from disk"""
        filepath = filepath or str(Path(settings.VECTORSTORE_PATH) / "faiss_index.bin")
        
        if not Path(filepath).exists():
            raise FileNotFoundError(f"Index file not found: {filepath}")
        
        # Load index
        self.index = faiss.read_index(filepath)
        
        # Load chunk IDs mapping
        mapping_file = filepath.replace(".bin", "_mapping.pkl")
        with open(mapping_file, "rb") as f:
            data = pickle.load(f)
            self.chunk_ids = data["chunk_ids"]
            self.dimension = data["dimension"]
        
        return {
            "vectors_loaded": len(self.chunk_ids),
            "dimension": self.dimension
        }
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get current index statistics"""
        if self.index is None:
            return {"status": "not_built"}
        
        return {
            "status": "ready",
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "chunk_count": len(self.chunk_ids)
        }