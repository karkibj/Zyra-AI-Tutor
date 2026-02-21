"""
Check what content is in the vector store
Run: python scripts/check_vector_store.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.vector_store_service import get_vector_store

def check_store():
    vector_store = get_vector_store()
    stats = vector_store.get_stats()
    
    print(f"\n📊 Vector Store Stats:")
    print(f"   Total vectors: {stats['total_vectors']}")
    
    # Try to inspect metadata
    print(f"\n🔍 Checking stored metadata...")
    
    # Get some sample vectors with metadata
    if hasattr(vector_store, 'metadata_list'):
        print(f"\n   Found {len(vector_store.metadata_list)} metadata entries")
        
        # Group by title
        titles = {}
        for meta in vector_store.metadata_list:
            title = meta.get('title', 'Unknown')
            if title not in titles:
                titles[title] = 0
            titles[title] += 1
        
        print(f"\n📚 Content breakdown:")
        for title, count in sorted(titles.items()):
            print(f"   {title}: {count} chunks")
    else:
        print("   ⚠️ Cannot access metadata directly")

if __name__ == "__main__":
    check_store()