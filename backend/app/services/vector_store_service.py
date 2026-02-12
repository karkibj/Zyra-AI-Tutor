"""
Vector Store Service
Manages FAISS vector database for semantic search
"""
import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json


class VectorStoreService:
    """Manage FAISS vector store"""
    
    def __init__(self, index_path: str = "data/vector_store"):
        """Initialize vector store"""
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.index_path / "faiss.index"
        self.metadata_file = self.index_path / "metadata.pkl"
        
        self.index: Optional[faiss.Index] = None
        self.metadata_list: List[Dict] = []  # ✅ RENAMED from metadata to metadata_list
        self.dimension: Optional[int] = None
        
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing index or create new one"""
        if self.index_file.exists() and self.metadata_file.exists():
            print("📂 Loading existing FAISS index...")
            self.index = faiss.read_index(str(self.index_file))
            with open(self.metadata_file, 'rb') as f:
                self.metadata_list = pickle.load(f)  # ✅ FIXED
            self.dimension = self.index.d
            print(f"✅ Loaded index with {self.index.ntotal} vectors (dim={self.dimension})")
            print(f"✅ Loaded {len(self.metadata_list)} metadata entries")  # ✅ VERIFY
        else:
            print("📝 No existing index found. Will create on first add.")
    
    def add_vectors(
        self,
        vectors: np.ndarray,
        metadata: List[Dict]
    ) -> List[int]:
        """Add vectors to index with metadata"""
        if len(vectors) == 0:
            return []
        
        # Create index if it doesn't exist
        if self.index is None:
            self.dimension = vectors.shape[1]
            self.index = faiss.IndexFlatL2(self.dimension)
            print(f"✨ Created new FAISS index (dim={self.dimension})")
        
        # Normalize vectors
        faiss.normalize_L2(vectors)
        
        # Get current size (for IDs)
        start_id = self.index.ntotal
        
        # Add to index
        self.index.add(vectors)
        
        # Add metadata
        for i, meta in enumerate(metadata):
            meta['vector_id'] = start_id + i
            self.metadata_list.append(meta)  # ✅ FIXED
        
        # ✅ ALWAYS SAVE AFTER ADDING
        self._save_index()
        
        print(f"✅ Added {len(vectors)} vectors with metadata")
        print(f"   Total vectors: {self.index.ntotal}")
        print(f"   Total metadata: {len(self.metadata_list)}")
        
        return list(range(start_id, start_id + len(vectors)))
    
    def search(
        self,
        query_vector: np.ndarray,
        k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar vectors"""
        if self.index is None or self.index.ntotal == 0:
            return []
        
        # Reshape and normalize query vector
        query = query_vector.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query)
        
        # Search
        search_k = k * 3 if filters else k
        distances, indices = self.index.search(query, min(search_k, self.index.ntotal))
        
        # Build results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                break
            
            # ✅ CHECK IF METADATA EXISTS FOR THIS INDEX
            if idx >= len(self.metadata_list):
                print(f"⚠️  No metadata for index {idx}")
                continue
            
            meta = self.metadata_list[idx].copy()  # ✅ FIXED
            meta['score'] = float(1 / (1 + dist))
            meta['distance'] = float(dist)
            
            # Apply filters
            if filters:
                match = all(
                    meta.get(key) == value
                    for key, value in filters.items()
                )
                if not match:
                    continue
            
            results.append(meta)
            
            if len(results) >= k:
                break
        
        return results
    
    def _save_index(self):
        """Save index and metadata to disk"""
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_file))
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.metadata_list, f)  # ✅ FIXED
            print(f"💾 Saved index and {len(self.metadata_list)} metadata entries")
    
    def get_stats(self) -> Dict:
        """Get vector store statistics"""
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'index_file_size': self.index_file.stat().st_size if self.index_file.exists() else 0,
            'metadata_count': len(self.metadata_list)  # ✅ FIXED
        }


# Global instance
_vector_store = None

def get_vector_store() -> VectorStoreService:
    """Get global vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store