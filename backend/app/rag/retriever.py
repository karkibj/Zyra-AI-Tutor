import os
from typing import List
from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.core.llm import get_embeddings


class DocumentRetriever:
    """Handles document loading, chunking, and retrieval."""
    
    def __init__(self, data_dir: str = "data/chapters"):
        self.data_dir = Path(data_dir)
        self.embeddings = get_embeddings()
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def load_documents(self, chapter: str = None) -> List[Document]:
        """
        Load documents from data directory.
        
        Args:
            chapter: Optional specific chapter to load (e.g., "money_exchange")
                    If None, loads all chapters
        """
        documents = []
        
        if chapter:
            # Load specific chapter
            chapter_file = self.data_dir / f"{chapter}.docx"
            if chapter_file.exists():
                loader = Docx2txtLoader(str(chapter_file))
                docs = loader.load()
                # Add metadata
                for doc in docs:
                    doc.metadata["chapter"] = chapter
                    doc.metadata["source"] = str(chapter_file)
                documents.extend(docs)
            else:
                print(f"Warning: Chapter file not found: {chapter_file}")
        else:
            # Load all .docx files from directory
            if self.data_dir.exists():
                for file_path in self.data_dir.glob("*.docx"):
                    loader = Docx2txtLoader(str(file_path))
                    docs = loader.load()
                    # Add metadata
                    chapter_name = file_path.stem
                    for doc in docs:
                        doc.metadata["chapter"] = chapter_name
                        doc.metadata["source"] = str(file_path)
                    documents.extend(docs)
            else:
                print(f"Warning: Data directory not found: {self.data_dir}")
        
        return documents
    
    def create_vectorstore(self, chapter: str = None):
        """Create or update vector store from documents."""
        documents = self.load_documents(chapter)
        
        if not documents:
            raise ValueError("No documents loaded. Please add curriculum materials to the data directory.")
        
        # Split documents into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        print(f"Loaded {len(documents)} documents, split into {len(chunks)} chunks")
        
        # Create FAISS vectorstore
        self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
        
        return self.vectorstore
    
    def retrieve(self, query: str, k: int = 4) -> List[Document]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: User's question
            k: Number of documents to retrieve
            
        Returns:
            List of relevant document chunks
        """
        if self.vectorstore is None:
            raise ValueError("Vectorstore not initialized. Call create_vectorstore() first.")
        
        # Retrieve similar documents
        docs = self.vectorstore.similarity_search(query, k=k)
        
        return docs
    
    def save_vectorstore(self, path: str = "backend/data/vectorstore"):
        """Save vectorstore to disk."""
        if self.vectorstore:
            self.vectorstore.save_local(path)
            print(f"Vectorstore saved to {path}")
    
    def load_vectorstore(self, path: str = "backend/data/vectorstore"):
        """Load vectorstore from disk."""
        if Path(path).exists():
            self.vectorstore = FAISS.load_local(
                path, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            print(f"Vectorstore loaded from {path}")
            return True
        return False