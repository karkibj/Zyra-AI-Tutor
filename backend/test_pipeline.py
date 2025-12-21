"""Test script for the RAG pipeline."""

from app.rag.pipeline import ZyraTutorPipeline

def test_pipeline():
    print("Initializing Zyra Pipeline...")
    pipeline = ZyraTutorPipeline()
    
    # Test cases
    test_queries = [
        ("Hi! How are you?", None),  # GREETING
        ("What is foreign exchange?", "money_exchange"),  # MATHEMATICAL_QUERY
        ("Can you explain that again?", None),  # CLARIFICATION
        ("What's the weather today?", None),  # OFF_TOPIC
        ("How do I calculate exchange rate?", "money_exchange"),  # MATHEMATICAL_QUERY
    ]
    
    for query, chapter in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"Chapter: {chapter}")
        print(f"{'='*60}")
        
        result = pipeline.process_query(query, chapter)
        
        print(f"Intent: {result['intent']}")
        print(f"Used RAG: {result['used_rag']}")
        print(f"\nResponse:\n{result['reply']}")
        
        if result.get('sources'):
            print(f"\nSources: {len(result['sources'])} documents used")

if __name__ == "__main__":
    test_pipeline()