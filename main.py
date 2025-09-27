"""
Main entry point for the ARGO AI Ocean Data Explorer.
Initializes the system and provides command-line interface.
"""

import argparse
import sys
import os
from datetime import datetime

from data_generator import ARGODataGenerator
from database import ARGODatabase
from vector_db import ARGOVectorDB
from rag_pipeline import ARGORAGPipeline
from config import INDIAN_OCEAN_BOUNDS

def setup_database(num_floats: int = 50, days_back: int = 365):
    """Set up the database with sample data."""
    print("Setting up ARGO AI system...")
    
    # Initialize database
    print("Initializing database...")
    db = ARGODatabase()
    
    # Initialize vector database
    print("Initializing vector database...")
    vector_db = ARGOVectorDB()
    
    # Generate sample data
    print(f"Generating sample data for {num_floats} floats...")
    generator = ARGODataGenerator(num_floats=num_floats, days_back=days_back)
    floats_data, profiles_data = generator.generate_all_data()
    
    # Insert data into database
    print("Inserting data into database...")
    db.insert_floats(floats_data)
    
    # Flatten profiles for database insertion
    profile_records = []
    for profile in profiles_data:
        for i, depth in enumerate(profile['depths']):
            record = {
                'profile_id': profile['profile_id'],
                'float_id': profile['float_id'],
                'timestamp': profile['timestamp'],
                'latitude': profile['latitude'],
                'longitude': profile['longitude'],
                'depth': depth
            }
            for param, values in profile['parameters'].items():
                record[param] = values[i]
            profile_records.append(record)
    
    db.insert_profiles(profile_records)
    
    # Add to vector database
    print("Indexing data in vector database...")
    for float_data in floats_data:
        profile_summary = db.get_profile_summary(float_data['float_id'])
        vector_db.add_float_data(float_data, profile_summary)
    
    vector_db.save_index()
    
    print("Setup complete!")
    return db, vector_db

def test_rag_system(db: ARGODatabase, vector_db: ARGOVectorDB):
    """Test the RAG system with sample queries."""
    print("\nTesting RAG system...")
    
    rag = ARGORAGPipeline(db, vector_db)
    
    # Sample queries
    test_queries = [
        "Show me temperature profiles near the equator",
        "What ARGO floats are active in the Indian Ocean?",
        "Compare salinity data from different regions",
        "Show me oxygen profiles from the last 6 months"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        result = rag.process_query(query)
        print(f"Response: {result['response']}")
        print(f"Data points found: {result['data_summary']['total_records']}")

def interactive_mode(db: ARGODatabase, vector_db: ARGOVectorDB):
    """Run interactive query mode."""
    print("\nInteractive mode - Type 'quit' to exit")
    print("=" * 50)
    
    rag = ARGORAGPipeline(db, vector_db)
    
    while True:
        try:
            query = input("\nEnter your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            print("\nProcessing...")
            result = rag.process_query(query)
            
            print(f"\nResponse: {result['response']}")
            
            if result['data_summary']['total_records'] > 0:
                print(f"\nData Summary:")
                print(f"- Total records: {result['data_summary']['total_records']}")
                print(f"- Parameters: {', '.join(result['data_summary']['parameters_found'])}")
                
                if result['data_summary']['geographic_bounds']:
                    bounds = result['data_summary']['geographic_bounds']
                    print(f"- Geographic bounds: {bounds['min_lat']:.2f}°N to {bounds['max_lat']:.2f}°N, "
                          f"{bounds['min_lon']:.2f}°E to {bounds['max_lon']:.2f}°E")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nGoodbye!")

def main():
    parser = argparse.ArgumentParser(description="ARGO AI Ocean Data Explorer")
    parser.add_argument("--setup", action="store_true", help="Set up the database with sample data")
    parser.add_argument("--floats", type=int, default=50, help="Number of floats to generate (default: 50)")
    parser.add_argument("--days", type=int, default=365, help="Days of data to generate (default: 365)")
    parser.add_argument("--test", action="store_true", help="Test the RAG system")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--dashboard", action="store_true", help="Launch Streamlit dashboard")
    parser.add_argument("--test-groq", action="store_true", help="Test Groq API integration")
    parser.add_argument("--backend", action="store_true", help="Start FastAPI backend server")
    parser.add_argument("--test-backend", action="store_true", help="Test FastAPI backend")
    parser.add_argument("--check-db", action="store_true", help="Check for existing database")
    
    args = parser.parse_args()
    
    if args.setup:
        db, vector_db = setup_database(args.floats, args.days)
        
        if args.test:
            test_rag_system(db, vector_db)
        
        if args.interactive:
            interactive_mode(db, vector_db)
    
    elif args.dashboard:
        print("Launching Streamlit dashboard...")
        print("The dashboard will open in your browser.")
        print("Press Ctrl+C to stop the server.")
        
        import subprocess
        try:
            subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard.py"], check=True)
        except KeyboardInterrupt:
            print("\nDashboard stopped.")
    
    elif args.test_groq:
        print("Testing Groq API integration...")
        try:
            from test_groq import main as test_groq_main
            test_groq_main()
        except ImportError:
            print("Error: test_groq.py not found")
        except Exception as e:
            print(f"Error running Groq test: {e}")
    
    elif args.backend:
        print("Starting FastAPI backend server...")
        try:
            import subprocess
            subprocess.run([sys.executable, "start_backend.py"], check=True)
        except KeyboardInterrupt:
            print("\nBackend stopped.")
        except Exception as e:
            print(f"Error starting backend: {e}")
    
    elif args.test_backend:
        print("Testing FastAPI backend...")
        try:
            from test_backend import main as test_backend_main
            test_backend_main()
        except ImportError:
            print("Error: test_backend.py not found")
        except Exception as e:
            print(f"Error running backend test: {e}")
    
    elif args.check_db:
        print("Checking for existing database...")
        try:
            from check_database import main as check_db_main
            check_db_main()
        except ImportError:
            print("Error: check_database.py not found")
        except Exception as e:
            print(f"Error checking database: {e}")
    
    elif args.test or args.interactive:
        # Load existing database
        try:
            db = ARGODatabase()
            vector_db = ARGOVectorDB()
            vector_db.load_index()
            
            if args.test:
                test_rag_system(db, vector_db)
            
            if args.interactive:
                interactive_mode(db, vector_db)
                
        except Exception as e:
            print(f"Error loading existing database: {e}")
            print("Please run with --setup first to create the database.")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
