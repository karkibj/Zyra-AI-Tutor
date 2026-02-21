"""
Inspect what's actually in the vector store
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.vector_store_service import get_vector_store

def inspect():
    vector_store = get_vector_store()
    
    print(f"\n📊 Vector Store Inspection")
    print(f"="*60)
    
    stats = vector_store.get_stats()
    print(f"Total vectors: {stats['total_vectors']:,}")
    
    # Check if metadata exists
    if hasattr(vector_store, 'metadata_list') and vector_store.metadata_list:
        print(f"\n✅ Metadata exists: {len(vector_store.metadata_list)} entries")
        
        # Count by title
        titles = {}
        types = {}
        
        for meta in vector_store.metadata_list:
            title = meta.get('title', 'Unknown')
            content_type = meta.get('content_type', 'Unknown')
            
            titles[title] = titles.get(title, 0) + 1
            types[content_type] = types.get(content_type, 0) + 1
        
        print(f"\n📚 By Title:")
        for title, count in sorted(titles.items()):
            print(f"   {title}: {count} chunks")
        
        print(f"\n📋 By Type:")
        for ctype, count in sorted(types.items()):
            print(f"   {ctype}: {count} chunks")
        
        # Show sample metadata
        print(f"\n🔍 Sample metadata (first 3):")
        for i, meta in enumerate(vector_store.metadata_list[:3]):
            print(f"\n   {i+1}. {meta}")
            
    else:
        print(f"\n❌ NO METADATA FOUND!")
        print(f"   The vectors exist but have no metadata attached")
        print(f"   This is why retrieval can't identify sources")

if __name__ == "__main__":
    inspect()