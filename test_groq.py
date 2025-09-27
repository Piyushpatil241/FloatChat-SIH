"""
Test script for Groq API integration with ARGO RAG system.
"""

import os
import sys
from config import GROQ_API_KEY

def test_groq_connection():
    """Test basic Groq API connection."""
    try:
        from groq import Groq
        
        if not GROQ_API_KEY:
            print("❌ GROQ_API_KEY not found in environment variables")
            print("Please set your Groq API key:")
            print("export GROQ_API_KEY='your_groq_api_key_here'")
            return False
        
        # Initialize Groq client
        client = Groq(api_key=GROQ_API_KEY)
        
        # Test with a simple query
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful oceanographic data assistant."},
                {"role": "user", "content": "What is ARGO data?"}
            ],
            max_tokens=100,
            temperature=0.3,
            top_p = 0.7
        )
        
        print("✅ Groq API connection successful!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except ImportError:
        print("❌ Groq package not installed")
        print("Please install it with: pip install groq")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Groq API: {e}")
        return False

def test_argo_rag_with_groq():
    """Test the ARGO RAG system with Groq."""
    try:
        from database import ARGODatabase
        from vector_db import ARGOVectorDB
        from rag_pipeline import ARGORAGPipeline
        
        print("\n🧪 Testing ARGO RAG system with Groq...")
        
        # Initialize systems
        db = ARGODatabase()
        vector_db = ARGOVectorDB()
        rag = ARGORAGPipeline(db, vector_db)
        
        # Test queries
        test_queries = [
            "What is ARGO data?",
            "Show me temperature data",
            "Tell me about ocean salinity"
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            print("-" * 50)
            
            result = rag.process_query(query)
            print(f"🤖 Response: {result['response']}")
            print(f"📊 Data points found: {result['data_summary']['total_records']}")
        
        print("\n✅ ARGO RAG system with Groq working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing ARGO RAG system: {e}")
        return False

def main():
    """Run all Groq tests."""
    print("🌊 ARGO AI System - Groq Integration Test")
    print("=" * 50)
    
    # Test Groq connection
    if not test_groq_connection():
        return
    
    # Test ARGO RAG system
    test_argo_rag_with_groq()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    main()
