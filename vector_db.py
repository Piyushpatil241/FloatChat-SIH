"""
Vector database setup for ARGO data using FAISS and ChromaDB.
Handles metadata indexing and similarity search for RAG pipeline.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
import json
import pickle
from datetime import datetime
import os

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("FAISS not available, using alternative vector storage")

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("ChromaDB not available, using alternative vector storage")

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from config import VECTOR_DB_PATH, CHROMA_PERSIST_DIRECTORY

class ARGOVectorDB:
    def __init__(self, use_chroma: bool = True):
        self.use_chroma = use_chroma and CHROMA_AVAILABLE
        self.vector_db_path = VECTOR_DB_PATH
        self.chroma_persist_dir = CHROMA_PERSIST_DIRECTORY
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except:
            print("Using TF-IDF as fallback for embeddings")
            self.embedding_model = None
            self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
        # Initialize vector database
        if self.use_chroma:
            self._init_chroma()
        else:
            self._init_faiss()
    
    def _init_chroma(self):
        """Initialize ChromaDB."""
        os.makedirs(self.chroma_persist_dir, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_persist_dir)
        
        # Create or get collection
        try:
            self.collection = self.chroma_client.get_collection("argo_metadata")
        except:
            self.collection = self.chroma_client.create_collection(
                name="argo_metadata",
                metadata={"description": "ARGO float metadata and summaries"}
            )
    
    def _init_faiss(self):
        """Initialize FAISS index."""
        os.makedirs(self.vector_db_path, exist_ok=True)
        self.index_path = os.path.join(self.vector_db_path, "argo_index.faiss")
        self.metadata_path = os.path.join(self.vector_db_path, "argo_metadata.pkl")
        
        # Load existing index or create new one
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            # Create new index (dimension will be set when first data is added)
            self.index = None
            self.metadata = []
    
    def _create_text_summary(self, float_data: Dict[str, Any], profile_summary: Dict[str, Any]) -> str:
        """Create a text summary for vector indexing."""
        summary_parts = [
            f"ARGO float {float_data['float_id']}",
            f"Platform: {float_data['platform_type']}",
            f"Status: {float_data['status']}",
            f"Location: {float_data['latitude']:.2f}°N, {float_data['longitude']:.2f}°E",
            f"Deployed: {float_data['deployment_date'].strftime('%Y-%m-%d')}",
            f"Institution: {float_data['institution']}"
        ]
        
        if profile_summary:
            summary_parts.extend([
                f"Total profiles: {profile_summary.get('total_profiles', 0)}",
                f"Depth range: {profile_summary.get('depth_range', {}).get('min', 0):.0f}-{profile_summary.get('depth_range', {}).get('max', 0):.0f}m",
                f"Temperature range: {profile_summary.get('temperature_stats', {}).get('min', 0):.1f}-{profile_summary.get('temperature_stats', {}).get('max', 0):.1f}°C",
                f"Salinity range: {profile_summary.get('salinity_stats', {}).get('min', 0):.1f}-{profile_summary.get('salinity_stats', {}).get('max', 0):.1f} PSU"
            ])
        
        return " | ".join(summary_parts)
    
    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for text data."""
        if self.embedding_model:
            return self.embedding_model.encode(texts)
        else:
            # Use TF-IDF as fallback
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            return tfidf_matrix.toarray()
    
    def add_float_data(self, float_data: Dict[str, Any], profile_summary: Dict[str, Any] = None):
        """Add float data to vector database."""
        text_summary = self._create_text_summary(float_data, profile_summary)
        embedding = self._get_embeddings([text_summary])[0]
        
        if self.use_chroma:
            self.collection.add(
                embeddings=[embedding.tolist()],
                documents=[text_summary],
                metadatas=[{
                    'float_id': float_data['float_id'],
                    'latitude': float_data['latitude'],
                    'longitude': float_data['longitude'],
                    'status': float_data['status'],
                    'platform_type': float_data['platform_type'],
                    'institution': float_data['institution']
                }],
                ids=[float_data['float_id']]
            )
        else:
            # Use FAISS
            if self.index is None:
                # Create new index
                dimension = len(embedding)
                self.index = faiss.IndexFlatL2(dimension)
            
            self.index.add(embedding.reshape(1, -1))
            self.metadata.append({
                'float_id': float_data['float_id'],
                'text_summary': text_summary,
                'metadata': {
                    'latitude': float_data['latitude'],
                    'longitude': float_data['longitude'],
                    'status': float_data['status'],
                    'platform_type': float_data['platform_type'],
                    'institution': float_data['institution']
                }
            })
    
    def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar floats based on query."""
        query_embedding = self._get_embeddings([query])[0]
        
        if self.use_chroma:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=k
            )
            
            similar_floats = []
            for i in range(len(results['ids'][0])):
                similar_floats.append({
                    'float_id': results['ids'][0][i],
                    'distance': results['distances'][0][i],
                    'text_summary': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i]
                })
            
            return similar_floats
        else:
            # Use FAISS
            if self.index is None:
                return []
            
            distances, indices = self.index.search(query_embedding.reshape(1, -1), k)
            
            similar_floats = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.metadata):
                    similar_floats.append({
                        'float_id': self.metadata[idx]['float_id'],
                        'distance': float(distance),
                        'text_summary': self.metadata[idx]['text_summary'],
                        'metadata': self.metadata[idx]['metadata']
                    })
            
            return similar_floats
    
    def get_float_by_location(self, lat: float, lon: float, radius: float = 1.0) -> List[Dict[str, Any]]:
        """Find floats near a specific location."""
        if self.use_chroma:
            # ChromaDB doesn't have built-in geographic search, so we'll use metadata filtering
            results = self.collection.get()
            nearby_floats = []
            
            for i, metadata in enumerate(results['metadatas']):
                float_lat = metadata['latitude']
                float_lon = metadata['longitude']
                
                # Simple distance calculation (not accurate for large distances)
                distance = ((lat - float_lat)**2 + (lon - float_lon)**2)**0.5
                
                if distance <= radius:
                    nearby_floats.append({
                        'float_id': results['ids'][i],
                        'distance': distance,
                        'text_summary': results['documents'][i],
                        'metadata': metadata
                    })
            
            return sorted(nearby_floats, key=lambda x: x['distance'])
        else:
            # FAISS approach
            nearby_floats = []
            for metadata in self.metadata:
                float_lat = metadata['metadata']['latitude']
                float_lon = metadata['metadata']['longitude']
                
                distance = ((lat - float_lat)**2 + (lon - float_lon)**2)**0.5
                
                if distance <= radius:
                    nearby_floats.append({
                        'float_id': metadata['float_id'],
                        'distance': distance,
                        'text_summary': metadata['text_summary'],
                        'metadata': metadata['metadata']
                    })
            
            return sorted(nearby_floats, key=lambda x: x['distance'])
    
    def save_index(self):
        """Save the vector index to disk."""
        if not self.use_chroma and self.index is not None:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            print(f"Vector index saved to {self.index_path}")
    
    def load_index(self):
        """Load the vector index from disk."""
        if not self.use_chroma and os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            print(f"Vector index loaded from {self.index_path}")

if __name__ == "__main__":
    # Test vector database
    vector_db = ARGOVectorDB()
    print("Vector database initialized successfully!")
