"""
Demo script for the complete ARGO AI system with both Streamlit and FastAPI frontends.
"""

import os
import sys
import time
import webbrowser
from pathlib import Path

def print_banner():
    """Print the system banner."""
    print("🌊" + "="*60 + "🌊")
    print("    ARGO AI Ocean Data Explorer - Complete System Demo")
    print("🌊" + "="*60 + "🌊")
    print()

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'streamlit', 'pandas', 'numpy', 
        'plotly', 'folium', 'groq', 'sqlalchemy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"{package}")
        except ImportError:
            print(f"{package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r requirements.txt")
        return False
    
    print("All dependencies found!")
    return True

def setup_system():
    """Set up the system with sample data."""
    print("\nSetting up system...")
    
    try:
        from data_generator import ARGODataGenerator
        from database import ARGODatabase
        from vector_db import ARGOVectorDB
        from rag_pipeline import ARGORAGPipeline
        
        # Initialize systems
        print("  - Initializing database...")
        db = ARGODatabase()
        
        print("  - Initializing vector database...")
        vector_db = ARGOVectorDB()
        
        print("  - Initializing RAG pipeline...")
        rag = ARGORAGPipeline(db, vector_db)
        
        # Check if data already exists
        existing_floats = db.query_floats()
        if len(existing_floats) > 0:
            print(f"  - Found existing data: {len(existing_floats)} floats")
            return True
        
        # Generate sample data
        print("  - Generating sample data...")
        generator = ARGODataGenerator(num_floats=20, days_back=180)
        floats_data, profiles_data = generator.generate_all_data()
        
        # Insert into database
        print("  - Inserting data into database...")
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
        print("  - Indexing data in vector database...")
        for float_data in floats_data:
            profile_summary = db.get_profile_summary(float_data['float_id'])
            vector_db.add_float_data(float_data, profile_summary)
        
        vector_db.save_index()
        
        print(f"System setup complete! Generated {len(floats_data)} floats and {len(profiles_data)} profiles.")
        return True
        
    except Exception as e:
        print(f"Error setting up system: {e}")
        return False

def demo_streamlit():
    """Demo the Streamlit frontend."""
    print("\nStreamlit Dashboard Demo")
    print("-" * 30)
    print("The Streamlit dashboard will open in your browser.")
    print("Features:")
    print("  - Interactive data overview")
    print("  - Geographic map visualization")
    print("  - Profile analysis and charts")
    print("  - AI chat assistant")
    print("  - Data export capabilities")
    print()
    
    choice = input("Open Streamlit dashboard? (y/n): ").lower().strip()
    if choice == 'y':
        print("Starting Streamlit dashboard...")
        print("   URL: http://localhost:8501")
        print("   Press Ctrl+C to stop")
        print()
        
        try:
            import subprocess
            subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard.py"], check=True)
        except KeyboardInterrupt:
            print("\nStreamlit dashboard stopped.")
        except Exception as e:
            print(f"Error starting Streamlit: {e}")

def demo_fastapi():
    """Demo the FastAPI frontend."""
    print("\nFastAPI Web Interface Demo")
    print("-" * 30)
    print("The FastAPI backend with HTML frontend will start.")
    print("Features:")
    print("  - Modern responsive web interface")
    print("  - Interactive Leaflet map")
    print("  - Plotly-powered visualizations")
    print("  - Real-time AI chat with Groq")
    print("  - RESTful API endpoints")
    print()
    print("URLs:")
    print("  - Frontend: http://localhost:8000")
    print("  - API Docs: http://localhost:8000/docs")
    print()
    
    choice = input("Start FastAPI backend? (y/n): ").lower().strip()
    if choice == 'y':
        print("   Starting FastAPI backend...")
        print("   Frontend: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        print("   Press Ctrl+C to stop")
        print()
        
        try:
            import subprocess
            subprocess.run([sys.executable, "start_backend.py"], check=True)
        except KeyboardInterrupt:
            print("\n👋 FastAPI backend stopped.")
        except Exception as e:
            print(f"Error starting FastAPI: {e}")

def demo_api():
    """Demo the API endpoints."""
    print("\nAPI Endpoints Demo")
    print("-" * 20)
    print("Available endpoints:")
    print("  GET  /health              - Health check")
    print("  GET  /api/stats           - System statistics")
    print("  GET  /api/floats          - List ARGO floats")
    print("  GET  /api/profiles        - List profiles with filters")
    print("  POST /api/query           - Natural language queries")
    print("  POST /api/generate-data   - Generate sample data")
    print("  GET  /api/export          - Export data")
    print()
    print("Full API documentation available at: http://localhost:8000/docs")

def main():
    """Main demo function."""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("\nPlease install missing dependencies first.")
        return
    
    # Setup system
    if not setup_system():
        print("\nSystem setup failed.")
        return
    
    print("\n🎉 System ready! Choose your demo:")
    print()
    print("1. Streamlit Dashboard (Python-based)")
    print("2. FastAPI Web Interface (HTML/CSS/JS)")
    print("3. API Documentation")
    print("4. All of the above")
    print("5. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            demo_streamlit()
        elif choice == '2':
            demo_fastapi()
        elif choice == '3':
            demo_api()
        elif choice == '4':
            print("\nStarting complete demo...")
            print("You can run both frontends simultaneously in different terminals:")
            print("  Terminal 1: python -m streamlit run dashboard.py")
            print("  Terminal 2: python start_backend.py")
            print()
            demo_streamlit()
        elif choice == '5':
            print("\n👋 Goodbye! Thanks for trying ARGO AI Explorer!")
            break
        else:
            print("Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main()
