"""
Test vector search directly
Run: python scripts/test_search.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.vector_store_service import get_vector_store
from app.services.embedding_service import get_embedding_service

def test_search():
    vector_store = get_vector_store()
    embedding_service = get_embedding_service()
    
    # Test query
    query = "quadratic equation model question example"
    
    print(f"🔍 Testing search for: '{query}'")
    
    # Generate embedding
    query_embedding = embedding_service.generate_embedding(query)
    print(f"   ✅ Generated query embedding")
    
    # Search
    results = vector_store.search(query_embedding, k=10)
    
    print(f"\n📊 Top 10 Results:")
    for i, result in enumerate(results, 1):
        print(f"\n   {i}. Score: {result['score']:.3f}")
        print(f"      Title: {result['metadata'].get('title', 'N/A')}")
        print(f"      Type: {result['metadata'].get('content_type', 'N/A')}")
        print(f"      Text preview: {result['metadata'].get('text', 'N/A')[:100]}...")

if __name__ == "__main__":
    test_search()