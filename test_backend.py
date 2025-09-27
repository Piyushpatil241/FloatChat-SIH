"""
Test script for the FastAPI backend.
"""

import requests
import json
import time
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_backend_endpoints():
    """Test all backend endpoints."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing ARGO AI Backend Endpoints")
    print("=" * 40)
    
    # Test health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is it running?")
        print("   Start it with: python start_backend.py")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test stats endpoint
    print("2. Testing stats endpoint...")
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Stats loaded: {stats['total_floats']} floats, {stats['total_profiles']} profiles")
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats error: {e}")
    
    # Test floats endpoint
    print("3. Testing floats endpoint...")
    try:
        response = requests.get(f"{base_url}/api/floats", timeout=10)
        if response.status_code == 200:
            floats = response.json()
            print(f"✅ Floats loaded: {len(floats)} floats")
        else:
            print(f"❌ Floats endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Floats error: {e}")
    
    # Test profiles endpoint
    print("4. Testing profiles endpoint...")
    try:
        response = requests.get(f"{base_url}/api/profiles?limit=10", timeout=10)
        if response.status_code == 200:
            profiles = response.json()
            print(f"✅ Profiles loaded: {len(profiles)} profiles")
        else:
            print(f"❌ Profiles endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Profiles error: {e}")
    
    # Test query endpoint
    print("5. Testing query endpoint...")
    try:
        query_data = {"query": "What is ARGO data?"}
        response = requests.post(
            f"{base_url}/api/query",
            json=query_data,
            timeout=15
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query processed: {result['response'][:100]}...")
        else:
            print(f"❌ Query endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Query error: {e}")
    
    # Test data generation
    print("6. Testing data generation...")
    try:
        response = requests.post(f"{base_url}/api/generate-data?num_floats=5&days_back=30", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Data generated: {result['floats_generated']} floats, {result['profiles_generated']} profiles")
        else:
            print(f"❌ Data generation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Data generation error: {e}")
    
    print("\n🎉 Backend testing completed!")
    return True

def main():
    """Main test function."""
    print("Starting backend tests...")
    print("Make sure the backend is running: python start_backend.py")
    print()
    
    # Wait a moment for user to start backend if needed
    input("Press Enter when the backend is running...")
    
    success = test_backend_endpoints()
    
    if success:
        print("\n✅ All tests passed! Backend is working correctly.")
        print("\nYou can now:")
        print("1. Open http://localhost:8000 in your browser")
        print("2. View API docs at http://localhost:8000/docs")
        print("3. Use the frontend interface")
    else:
        print("\n❌ Some tests failed. Please check the backend logs.")

if __name__ == "__main__":
    main()
