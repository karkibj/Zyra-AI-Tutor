"""
Document Processor - Handles PDF upload to database storage pipeline
"""
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import PyPDF2
import io

from app.services.document_service import DocumentService
from app.services.chunk_service import ChunkService
from app.core.config import settings


class DocumentProcessor:
    """Processes documents from upload through chunking and storage"""

    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    @staticmethod
    def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller segments with overlap
        Returns list of chunk dictionaries with metadata
        """
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Calculate end position
            end = start + chunk_size
            
            # Get chunk content
            chunk_content = text[start:end].strip()
            
            # Skip empty chunks
            if not chunk_content:
                start = end - overlap
                continue
            
            # Count tokens (approximate: 1 token ≈ 4 characters)
            token_count = len(chunk_content) // 4
            
            # Determine chunk type (basic heuristic)
            chunk_type = "text"
            if any(symbol in chunk_content for symbol in ["=", "+", "-", "×", "÷", "²", "³"]):
                if chunk_content.count("=") > 2:
                    chunk_type = "formula"
            
            chunks.append({
                "chunk_index": chunk_index,
                "content": chunk_content,
                "token_count": token_count,
                "chunk_type": chunk_type,
                "start_index": start,
                "end_index": end,
                "meta_data": {
                    "length": len(chunk_content),
                    "has_formulas": chunk_type == "formula"
                }
            })
            
            chunk_index += 1
            start = end - overlap
        
        return chunks

    @staticmethod
    async def process_document(
        db: AsyncSession,
        file_content: bytes,
        filename: str,
        chapter_id: uuid.UUID,
        subject_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete document processing pipeline:
        1. Create document record
        2. Extract text from PDF
        3. Chunk text
        4. Store chunks in database
        
        Returns: {document_id, chunk_count, status}
        """
        try:
            # Step 1: Create document record
            document = await DocumentService.create_document(
                db=db,
                chapter_id=chapter_id,
                subject_id=subject_id,
                uploaded_by=uploaded_by,
                title=title or filename,
                description=description,
                language="en",
                doc_type="pdf",
                status="processing"
            )
            
            # Step 2: Extract text
            text = DocumentProcessor.extract_text_from_pdf(file_content)
            
            if not text or len(text) < settings.MIN_CHUNK_SIZE:
                # Update document status to failed
                await DocumentService.update_document_status(db, document.document_id, "failed")
                raise ValueError("Insufficient text content in PDF")
            
            # Step 3: Chunk text
            chunks_data = DocumentProcessor.chunk_text(text)
            
            # Add document_id to each chunk
            for chunk in chunks_data:
                chunk["document_id"] = document.document_id
            
            # Step 4: Store chunks in database
            chunks = await ChunkService.create_chunks_batch(db, chunks_data)
            
            # Step 5: Update document status
            await DocumentService.update_document_status(db, document.document_id, "completed")
            
            return {
                "document_id": str(document.document_id),
                "title": document.title,
                "chunk_count": len(chunks),
                "total_tokens": sum(c.token_count for c in chunks),
                "status": "completed",
                "text_length": len(text)
            }
            
        except Exception as e:
            # Update document status if it exists
            if 'document' in locals():
                await DocumentService.update_document_status(
                    db, document.document_id, "failed"
                )
            raise ValueError(f"Document processing failed: {str(e)}")

    @staticmethod
    async def get_document_chunks(
        db: AsyncSession,
        document_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get all chunks for a document with their content"""
        chunks = await ChunkService.get_chunks_by_document(db, document_id)
        
        return [
            {
                "chunk_id": str(chunk.chunk_id),
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "token_count": chunk.token_count,
                "chunk_type": chunk.chunk_type
            }
            for chunk in chunks
        ]