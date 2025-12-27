"""
Embedding Generator - Creates and stores embeddings for chunks
"""
import uuid
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer
import numpy as np

from app.services.chunk_service import ChunkService
from app.services.embedding_service import EmbeddingService
from app.core.config import settings


class EmbeddingGenerator:
    """Generates and manages embeddings for document chunks"""
    
    # Class-level model instance (loaded once, reused)
    _model = None
    
    @classmethod
    def get_model(cls):
        """Get or load the embedding model (singleton pattern)"""
        if cls._model is None:
            print(f"📥 Loading embedding model: {settings.EMBEDDING_MODEL}")
            cls._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            print(f"✅ Model loaded successfully")
        return cls._model
    
    @staticmethod
    def generate_embedding(text: str) -> List[float]:
        """Generate embedding for a single text"""
        model = EmbeddingGenerator.get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    @staticmethod
    def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (more efficient)"""
        model = EmbeddingGenerator.get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return [emb.tolist() for emb in embeddings]
    
    @staticmethod
    async def create_embeddings_for_document(
        db: AsyncSession,
        document_id: uuid.UUID,
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """
        Generate and store embeddings for all chunks in a document
        
        Args:
            db: Database session
            document_id: Document UUID
            batch_size: Number of chunks to process at once
            
        Returns: {embeddings_created, document_id, model_name}
        """
        # Get all chunks for the document
        chunks = await ChunkService.get_chunks_by_document(db, document_id)
        
        if not chunks:
            raise ValueError(f"No chunks found for document {document_id}")
        
        print(f"📊 Generating embeddings for {len(chunks)} chunks...")
        
        # Extract texts and chunk_ids
        texts = [chunk.content for chunk in chunks]
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        
        # Generate embeddings in batches
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = EmbeddingGenerator.generate_embeddings_batch(batch_texts)
            all_embeddings.extend(batch_embeddings)
        
        # Prepare embedding data for database
        embeddings_data = [
            {
                "chunk_id": chunk_ids[i],
                "embedding_vector": all_embeddings[i],
                "model_name": settings.EMBEDDING_MODEL
            }
            for i in range(len(chunks))
        ]
        
        # Store embeddings in database
        print(f"💾 Storing {len(embeddings_data)} embeddings in database...")
        embeddings = await EmbeddingService.create_embeddings_batch(db, embeddings_data)
        
        return {
            "embeddings_created": len(embeddings),
            "document_id": str(document_id),
            "model_name": settings.EMBEDDING_MODEL,
            "embedding_dimension": len(all_embeddings[0]) if all_embeddings else 0
        }
    
    @staticmethod
    async def create_embeddings_for_chunks(
        db: AsyncSession,
        chunk_ids: List[uuid.UUID]
    ) -> Dict[str, Any]:
        """
        Generate and store embeddings for specific chunks
        Useful for incremental updates
        """
        embeddings_created = 0
        
        for chunk_id in chunk_ids:
            # Get chunk
            chunk = await ChunkService.get_chunk(db, chunk_id)
            if not chunk:
                continue
            
            # Check if embedding already exists
            existing = await EmbeddingService.get_embedding_by_chunk(db, chunk_id)
            if existing:
                continue
            
            # Generate embedding
            embedding_vector = EmbeddingGenerator.generate_embedding(chunk.content)
            
            # Store in database
            await EmbeddingService.create_embedding(
                db=db,
                chunk_id=chunk_id,
                embedding_vector=embedding_vector,
                model_name=settings.EMBEDDING_MODEL
            )
            
            embeddings_created += 1
        
        return {
            "embeddings_created": embeddings_created,
            "chunks_processed": len(chunk_ids)
        }
    
    @staticmethod
    async def get_document_embeddings(
        db: AsyncSession,
        document_id: uuid.UUID
    ) -> tuple[List[List[float]], List[uuid.UUID], List[str]]:
        """
        Get all embeddings for a document
        
        Returns: (embeddings, chunk_ids, contents)
        """
        # Get embeddings with chunks loaded
        embeddings = await EmbeddingService.get_embeddings_by_document(db, document_id)
        
        if not embeddings:
            return [], [], []
        
        # Extract data
        embedding_vectors = [emb.embedding_vector for emb in embeddings]
        chunk_ids = [emb.chunk_id for emb in embeddings]
        contents = [emb.chunk.content for emb in embeddings]
        
        return embedding_vectors, chunk_ids, contents