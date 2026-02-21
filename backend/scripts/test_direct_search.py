"""
Test direct search to see what's actually being retrieved
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.vector_store_service import get_vector_store
from app.services.embedding_service import get_embedding_service

def test_search():
    vector_store = get_vector_store()
    embedding_service = get_embedding_service()
    
    # Test queries
    queries = [
        "practice question from model paper",
        "quadratic equation model question",
        "SEE model question mathematics"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"🔍 Query: '{query}'")
        print(f"{'='*60}")
        
        # Generate embedding
        query_embedding = embedding_service.generate_embedding(query)
        
        # Search
        results = vector_store.search(query_embedding, k=10)
        
        print(f"\n📊 Top 10 Results:")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result['score']:.3f}")
            print(f"   Title: {result.get('title', 'N/A')}")
            print(f"   Type: {result.get('content_type', 'N/A')}")
            print(f"   Chunk: {result.get('chunk_index', 'N/A')}")
            print(f"   Text: {result.get('text', 'N/A')[:100]}...")
        
        print()

if __name__ == "__main__":
    test_search()