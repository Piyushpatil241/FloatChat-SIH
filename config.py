import os
from dotenv import load_dotenv

load_dotenv()

# LLM API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = "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"

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
