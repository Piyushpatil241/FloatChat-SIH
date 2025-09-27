"""
Configuration template for ARGO AI system.
Copy this file to config_local.py and modify as needed.
"""

import os

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///argo_data.db")

# Vector Database Configuration
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./vector_db")
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

# Application Configuration
STREAMLIT_SERVER_PORT = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# ARGO Data Configuration
INDIAN_OCEAN_BOUNDS = {
    "min_lat": -30,
    "max_lat": 30,
    "min_lon": 20,
    "max_lon": 120
}

# Sample ARGO float parameters
ARGO_PARAMETERS = [
    "temperature", "salinity", "pressure", "oxygen", "nitrate", 
    "chlorophyll", "backscatter", "downwelling_irradiance"
]

# Example environment variables to set:
# export OPENAI_API_KEY="your_api_key_here"
# export DATABASE_URL="postgresql://user:pass@localhost:5432/argo_data"
# export DEBUG="True"
