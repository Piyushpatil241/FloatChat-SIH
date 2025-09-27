"""
Setup script for Groq API integration.
Helps users configure their Groq API key and test the connection.
"""

import os
import sys
from pathlib import Path

def setup_groq_api_key():
    """Interactive setup for Groq API key."""
    print("ARGO AI System - Groq API Setup")
    print("=" * 40)
    
    # Check if API key already exists
    existing_key = "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"
    if existing_key:
        print(f"GROQ_API_KEY already set: {existing_key[:8]}...")
        choice = input("Do you want to update it? (y/n): ").lower().strip()
        if choice != 'y':
            return existing_key
    
    print("\nTo get your Groq API key:")
    print("1. Visit: https://console.groq.com/")
    print("2. Sign up or log in")
    print("3. Go to API Keys section")
    print("4. Create a new API key")
    print("5. Copy the key")
    
    print("\n" + "="*40)
    api_key = input("Enter your Groq API key: ").strip()
    
    if not api_key:
        print("No API key provided. Exiting.")
        return None
    
    # Validate API key format (basic check)
    if not api_key.startswith('gsk_'):
        print("Warning: Groq API keys usually start with 'gsk_'. Please verify your key.")
        confirm = input("Continue anyway? (y/n): ").lower().strip()
        if confirm != 'y':
            return None
    
    # Save to .env file
    env_file = Path(".env")
    env_content = []
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.readlines()
    
    # Update or add GROQ_API_KEY
    updated = False
    for i, line in enumerate(env_content):
        if line.startswith("GROQ_API_KEY="):
            env_content[i] = f"GROQ_API_KEY={api_key}\n"
            updated = True
            break
    
    if not updated:
        env_content.append(f"GROQ_API_KEY={api_key}\n")
    
    with open(env_file, 'w') as f:
        f.writelines(env_content)
    
    print(f"✅ API key saved to {env_file}")
    
    # Set environment variable for current session
    os.environ["GROQ_API_KEY"] = api_key
    
    return api_key

def test_groq_connection(api_key):
    """Test the Groq API connection."""
    print("\nTesting Groq API connection...")
    
    try:
        from groq import Groq
        
        client = Groq(api_key=api_key)
        
        # Test with a simple query
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello from Groq!' if you can hear me."}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        print("Groq API connection successful!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except ImportError:
        print("Groq package not installed")
        print("Installing groq package...")
        import subprocess
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "groq"], check=True)
            print("Groq package installed successfully!")
            return test_groq_connection(api_key)  # Retry
        except Exception as e:
            print(f"Failed to install groq package: {e}")
            return False
    except Exception as e:
        print(f"Error connecting to Groq API: {e}")
        return False

def main():
    """Main setup function."""
    print("Setting up Groq API for ARGO AI System...")
    
    # Setup API key
    api_key = setup_groq_api_key()
    if not api_key:
        print("Setup cancelled.")
        return
    
    # Test connection
    if test_groq_connection(api_key):
        print("\nGroq API setup completed successfully!")
        print("\nYou can now run the ARGO AI system with Groq integration:")
        print("  python main.py --setup")
        print("  python main.py --dashboard")
        print("  python test_groq.py")
    else:
        print("\nSetup failed. Please check your API key and try again.")

if __name__ == "__main__":
    main()
