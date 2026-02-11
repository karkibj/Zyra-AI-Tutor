"""
Text Extraction Service
Extracts text from PDFs and creates intelligent chunks
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Optional
import re


class TextExtractionService:
    """Extract and chunk text from PDFs"""
    
    @staticmethod
    def extract_from_pdf(file_path: str) -> Dict:
        """
        Extract text from PDF with metadata
        
        Returns:
            {
                'full_text': str,
                'pages': [{'page_num': int, 'text': str}],
                'total_pages': int,
                'metadata': dict
            }
        """
        doc = None
        try:
            pdf_path = Path(file_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF not found: {file_path}")
            
            # Open PDF
            doc = fitz.open(str(pdf_path))
            
            pages_data = []
            full_text = ""
            total_pages = len(doc)
            
            print(f"   📖 Reading {total_pages} pages...")
            
            for page_num in range(total_pages):
                page = doc[page_num]
                text = page.get_text()
                
                # Clean text
                text = TextExtractionService._clean_text(text)
                
                pages_data.append({
                    'page_num': page_num + 1,
                    'text': text
                })
                
                full_text += text + "\n\n"
                
                # Progress indicator
                if (page_num + 1) % 50 == 0:
                    print(f"   ... processed {page_num + 1}/{total_pages} pages")
            
            result = {
                'full_text': full_text.strip(),
                'pages': pages_data,
                'total_pages': total_pages,
                'metadata': {
                    'char_count': len(full_text),
                    'estimated_tokens': len(full_text) // 4
                }
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
        
        finally:
            # Always close document
            if doc is not None:
                try:
                    doc.close()
                except:
                    pass
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers (common patterns)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Remove extra newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    @staticmethod
    def create_chunks(
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Create intelligent text chunks
        
        Args:
            text: Full text to chunk
            chunk_size: Target size in characters
            chunk_overlap: Overlap between chunks
            metadata: Additional metadata for each chunk
            
        Returns:
            List of chunks with metadata
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Calculate end position
            end = start + chunk_size
            
            # If not at the end, try to break at sentence boundary
            if end < len(text):
                # Look for sentence end (., !, ?)
                sentence_end = max(
                    text.rfind('.', start, end),
                    text.rfind('!', start, end),
                    text.rfind('?', start, end)
                )
                
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk_data = {
                    'chunk_index': chunk_index,
                    'text': chunk_text,
                    'start_pos': start,
                    'end_pos': end,
                    'char_count': len(chunk_text),
                    'metadata': metadata or {}
                }
                chunks.append(chunk_data)
                chunk_index += 1
            
            # Move start position (with overlap)
            start = end - chunk_overlap if end < len(text) else end
        
        return chunks
    
    @staticmethod
    def extract_questions_from_text(text: str) -> List[Dict]:
        """
        Extract questions from text (for past papers)
        Detects question patterns
        """
        questions = []
        
        # Pattern for questions like: 1., 2(a), Q1, etc.
        question_pattern = r'(?:^|\n)(\d+\.?\s*(?:\([a-z]\))?)\s*(.+?)(?=\n\d+\.?(?:\s*\([a-z]\))?|\Z)'
        
        matches = re.finditer(question_pattern, text, re.MULTILINE | re.DOTALL)
        
        for idx, match in enumerate(matches):
            question_num = match.group(1).strip()
            question_text = match.group(2).strip()
            
            # Clean question text
            question_text = re.sub(r'\s+', ' ', question_text)
            
            if len(question_text) > 20:  # Avoid false positives
                questions.append({
                    'question_number': question_num,
                    'text': question_text,
                    'index': idx
                })
        
        return questions