"""
Script to check for existing ARGO database and help locate it.
"""

import os
import sys
from pathlib import Path
import sqlite3

def find_database_files():
    """Find all SQLite database files in the current directory and subdirectories."""
    db_files = []
    
    # Check current directory
    for file in Path('.').glob('*.db'):
        db_files.append(str(file.absolute()))
    
    # Check subdirectories
    for file in Path('.').glob('**/*.db'):
        if file.is_file():
            db_files.append(str(file.absolute()))
    
    return db_files

def check_database_content(db_path):
    """Check if a database contains ARGO data."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if argo_floats table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='argo_floats'")
        if not cursor.fetchone():
            return False, "No argo_floats table found"
        
        # Check if argo_profiles table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='argo_profiles'")
        if not cursor.fetchone():
            return False, "No argo_profiles table found"
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM argo_floats")
        float_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM argo_profiles")
        profile_count = cursor.fetchone()[0]
        
        conn.close()
        
        return True, f"Found {float_count} floats and {profile_count} profiles"
        
    except Exception as e:
        return False, f"Error reading database: {e}"

def main():
    print("🔍 ARGO Database Checker")
    print("=" * 30)
    
    # Find database files
    print("Searching for database files...")
    db_files = find_database_files()
    
    if not db_files:
        print("❌ No .db files found in current directory or subdirectories")
        print("\nTo create a new database, run:")
        print("  python main.py --setup --floats 20 --days 180")
        return
    
    print(f"Found {len(db_files)} database file(s):")
    
    argo_databases = []
    
    for db_file in db_files:
        print(f"\n📁 {db_file}")
        is_argo, message = check_database_content(db_file)
        
        if is_argo:
            print(f"✅ {message}")
            argo_databases.append(db_file)
        else:
            print(f"❌ {message}")
    
    if argo_databases:
        print(f"\n🎉 Found {len(argo_databases)} ARGO database(s):")
        for db in argo_databases:
            print(f"  - {db}")
        
        print("\n✅ Your database is ready!")
        print("You can now start the backend with:")
        print("  python main.py --backend")
        print("  or")
        print("  python start_backend.py")
    else:
        print("\n❌ No ARGO databases found")
        print("To create a new database, run:")
        print("  python main.py --setup --floats 20 --days 180")

if __name__ == "__main__":
    main()
