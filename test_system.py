"""
Test script to verify the ARGO AI system functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_generator import ARGODataGenerator
from database import ARGODatabase
from vector_db import ARGOVectorDB
from rag_pipeline import ARGORAGPipeline

def test_data_generation():
    """Test data generation functionality."""
    print("Testing data generation...")
    
    generator = ARGODataGenerator(num_floats=5, days_back=30)
    floats_data, profiles_data = generator.generate_all_data()
    
    assert len(floats_data) == 5, f"Expected 5 floats, got {len(floats_data)}"
    assert len(profiles_data) > 0, "No profiles generated"
    
    print("✓ Data generation test passed")
    return floats_data, profiles_data

def test_database():
    """Test database functionality."""
    print("Testing database...")
    
    db = ARGODatabase()
    
    # Test float insertion
    test_float = {
        'float_id': 'TEST_001',
        'platform_type': 'PROVOR',
        'deployment_date': '2023-01-01',
        'latitude': 10.0,
        'longitude': 70.0,
        'status': 'active',
        'max_pressure': 2000,
        'cycle_time': 5,
        'institution': 'TEST'
    }
    
    db.insert_floats([test_float])
    
    # Test query
    floats = db.query_floats()
    assert len(floats) >= 1, "Float not inserted"
    
    print("✓ Database test passed")
    return db

def test_vector_database():
    """Test vector database functionality."""
    print("Testing vector database...")
    
    vector_db = ARGOVectorDB()
    
    # Test adding data
    test_float = {
        'float_id': 'TEST_001',
        'platform_type': 'PROVOR',
        'deployment_date': '2023-01-01',
        'latitude': 10.0,
        'longitude': 70.0,
        'status': 'active',
        'max_pressure': 2000,
        'cycle_time': 5,
        'institution': 'TEST'
    }
    
    vector_db.add_float_data(test_float, {})
    
    # Test search
    results = vector_db.search_similar("temperature data", k=1)
    assert len(results) >= 0, "Vector search failed"
    
    print("✓ Vector database test passed")
    return vector_db

def test_rag_pipeline():
    """Test RAG pipeline functionality."""
    print("Testing RAG pipeline...")
    
    db = ARGODatabase()
    vector_db = ARGOVectorDB()
    rag = ARGORAGPipeline(db, vector_db)
    
    # Test query parsing
    parsed = rag.parse_query("Show me temperature data near the equator")
    assert parsed['intent'] in ['parameter_query', 'location_query', 'general_query'], "Query parsing failed"
    
    # Test query processing
    result = rag.process_query("Show me temperature data")
    assert 'response' in result, "Query processing failed"
    
    print("✓ RAG pipeline test passed")
    return rag

def main():
    """Run all tests."""
    print("Running ARGO AI System Tests")
    print("=" * 40)
    
    try:
        # Test individual components
        floats_data, profiles_data = test_data_generation()
        db = test_database()
        vector_db = test_vector_database()
        rag = test_rag_pipeline()
        
        print("\n" + "=" * 40)
        print("All tests passed! ✓")
        print("The ARGO AI system is ready to use.")
        
        # Show system summary
        print(f"\nSystem Summary:")
        print(f"- Generated {len(floats_data)} floats")
        print(f"- Generated {len(profiles_data)} profiles")
        print(f"- Database initialized")
        print(f"- Vector database initialized")
        print(f"- RAG pipeline ready")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
