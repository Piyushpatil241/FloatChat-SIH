"""
Demo script showing ARGO AI system with Groq integration.
"""

import os
import sys
from datetime import datetime

def demo_groq_argo_system():
    """Demonstrate the ARGO AI system with Groq."""
    print("ARGO AI Ocean Data Explorer - Groq Demo")
    print("=" * 50)
    
    # Check if Groq is available
    try:
        from groq import Groq
        from config import GROQ_API_KEY
        
        if not GROQ_API_KEY:
            print("GROQ_API_KEY not found!")
            print("Please run: python setup_groq.py")
            return False
        
        print("Groq API key found")
        
    except ImportError:
        print("Groq package not installed")
        print("Please install: pip install groq")
        return False
    
    # Initialize the system
    print("\nInitializing ARGO AI system...")
    try:
        from database import ARGODatabase
        from vector_db import ARGOVectorDB
        from rag_pipeline import ARGORAGPipeline
        
        db = ARGODatabase()
        vector_db = ARGOVectorDB()
        rag = ARGORAGPipeline(db, vector_db)
        
        print("System initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing system: {e}")
        return False
    
    # Demo queries
    print("\nDemo Queries with Groq:")
    print("-" * 30)
    
    demo_queries = [
        "What is ARGO data and how does it work?",
        "Tell me about ocean temperature measurements",
        "How do ARGO floats measure salinity?",
        "What are the benefits of ARGO data for ocean research?"
    ]
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n{i}. Query: {query}")
        print("-" * 40)
        
        try:
            result = rag.process_query(query)
            print(f"Groq Response: {result['response']}")
            print(f"Data points found: {result['data_summary']['total_records']}")
            
        except Exception as e:
            print(f"Error processing query: {e}")
    
    print("\nDemo completed successfully!")
    print("\nNext steps:")
    print("1. Set up sample data: python main.py --setup")
    print("2. Launch dashboard: python main.py --dashboard")
    print("3. Run interactive mode: python main.py --interactive")
    
    return True

def main():
    """Main demo function."""
    success = demo_groq_argo_system()
    
    if not success:
        print("\nDemo failed. Please check the setup and try again.")
        sys.exit(1)
    else:
        print("\nDemo completed successfully!")

if __name__ == "__main__":
    main()
