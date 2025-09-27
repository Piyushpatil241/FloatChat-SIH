"""
Start the ARGO AI system with existing database.
This script will find and use your existing database without regenerating data.
"""

import os
import sys
from pathlib import Path

def find_existing_database():
    """Find existing ARGO database."""
    # Check common locations
    possible_locations = [
        "argo_data.db",
        "./argo_data.db",
        "../argo_data.db",
        "data/argo_data.db",
        "./data/argo_data.db"
    ]
    
    for location in possible_locations:
        if os.path.exists(location):
            return os.path.abspath(location)
    
    return None

def update_database_config(db_path):
    """Update the database configuration to use the found database."""
    config_file = "config.py"
    
    if not os.path.exists(config_file):
        print(" config.py not found")
        return False
    
    # Read current config
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Update DATABASE_URL
    import re
    pattern = r'DATABASE_URL = os\.getenv\("DATABASE_URL", "[^"]*"\)'
    replacement = f'DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///{db_path}")'
    
    if re.search(pattern, content):
        new_content = re.sub(pattern, replacement, content)
        
        with open(config_file, 'w') as f:
            f.write(new_content)
        
        print(f" Updated config.py to use database: {db_path}")
        return True
    else:
        print(" Could not update config.py")
        return False

def main():
    print("🌊 ARGO AI - Starting with Existing Database")
    print("=" * 45)
    
    # Find existing database
    print(" Looking for existing database...")
    db_path = find_existing_database()
    
    if not db_path:
        print(" No existing database found")
        print("\nTo create a new database, run:")
        print("  python main.py --setup --floats 20 --days 180")
        print("\nOr to check for databases in other locations:")
        print("  python main.py --check-db")
        return
    
    print(f" Found existing database: {db_path}")
    
    # Update config if needed
    if not db_path.endswith("argo_data.db"):
        print("📝 Updating configuration...")
        if not update_database_config(db_path):
            print("  Could not update config, but database should still work")
    
    print("\n Starting FastAPI backend...")
    print("   Frontend: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("   Press Ctrl+C to stop")
    print()
    
    try:
        import subprocess
        subprocess.run([sys.executable, "start_backend.py"], check=True)
    except KeyboardInterrupt:
        print("\n Backend stopped.")
    except Exception as e:
        print(f" Error starting backend: {e}")

if __name__ == "__main__":
    main()
