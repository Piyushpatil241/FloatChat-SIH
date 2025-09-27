"""
FastAPI backend for ARGO AI Ocean Data Explorer.
Provides REST API endpoints for the frontend.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import json
from datetime import datetime, timedelta
import os
import sys


# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import ARGODatabase
from vector_db import ARGOVectorDB
from rag_pipeline import ARGORAGPipeline
from data_generator import ARGODataGenerator

# Initialize FastAPI app
app = FastAPI(
    title="ARGO AI Ocean Data Explorer API",
    description="AI-powered conversational system for ARGO float oceanographic data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for database connections
# Global variables
db = None
vector_db = None
rag = None

# Pydantic models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    response: str
    data_summary: Dict[str, Any]
    data: List[Dict[str, Any]]
    vector_results: List[Dict[str, Any]]

class FloatData(BaseModel):
    float_id: str
    platform_type: str
    deployment_date: str
    latitude: float
    longitude: float
    status: str
    max_pressure: int
    cycle_time: int
    institution: str

class ProfileData(BaseModel):
    profile_id: str
    float_id: str
    timestamp: str
    latitude: float
    longitude: float
    depth: float
    temperature: Optional[float] = None
    salinity: Optional[float] = None
    pressure: Optional[float] = None
    oxygen: Optional[float] = None
    nitrate: Optional[float] = None
    chlorophyll: Optional[float] = None
    backscatter: Optional[float] = None
    downwelling_irradiance: Optional[float] = None

class SystemStats(BaseModel):
    total_floats: int
    total_profiles: int
    active_floats: int
    latest_data: Optional[str] = None

# Initialize database connections
@app.on_event("startup")
async def startup_event():
    global db, vector_db, rag
    db = ARGODatabase()
    vector_db = ARGOVectorDB()
    rag = ARGORAGPipeline(db, vector_db)
    print("✅ RAG pipeline initialized")


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# System statistics
@app.get("/api/stats", response_model=SystemStats)
async def get_system_stats():
    try:
        floats_data = db.query_floats()
        profiles_data = db.query_profiles()
        active_floats = len(db.query_floats({'status': 'active'}))
        
        latest_data = None
        if not profiles_data.empty:
            latest_profile = profiles_data.sort_values('timestamp', ascending=False).iloc[0]
            latest_data = latest_profile['timestamp'].strftime('%Y-%m-%d')
        
        return SystemStats(
            total_floats=len(floats_data),
            total_profiles=len(profiles_data),
            active_floats=active_floats,
            latest_data=latest_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get all floats
@app.get("/api/floats", response_model=List[FloatData])
async def get_floats(
    status: Optional[str] = Query(None, description="Filter by status"),
    institution: Optional[str] = Query(None, description="Filter by institution")
):
    try:
        filters = {}
        if status:
            filters['status'] = status
        if institution:
            filters['institution'] = institution
        
        floats_data = db.query_floats(filters)
        return [FloatData(**row) for _, row in floats_data.iterrows()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get profiles with filters
@app.get("/api/profiles", response_model=List[ProfileData])
async def get_profiles(
    float_id: Optional[str] = Query(None, description="Filter by float ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    min_lat: Optional[float] = Query(None, description="Minimum latitude"),
    max_lat: Optional[float] = Query(None, description="Maximum latitude"),
    min_lon: Optional[float] = Query(None, description="Minimum longitude"),
    max_lon: Optional[float] = Query(None, description="Maximum longitude"),
    min_depth: Optional[float] = Query(None, description="Minimum depth"),
    max_depth: Optional[float] = Query(None, description="Maximum depth"),
    parameter: Optional[str] = Query(None, description="Filter by parameter"),
    limit: int = Query(1000, description="Maximum number of records")
):
    try:
        filters = {}
        
        if float_id:
            filters['float_id'] = float_id
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                filters['date_range'] = (start_dt, end_dt)
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=f"Invalid date format: {ve}")
        if min_lat is not None and max_lat is not None:
            filters['lat_range'] = (min_lat, max_lat)
        if min_lon is not None and max_lon is not None:
            filters['lon_range'] = (min_lon, max_lon)
        if min_depth is not None and max_depth is not None:
            filters['depth_range'] = (min_depth, max_depth)
        if parameter:
            filters['parameter'] = parameter
        
        profiles_data = db.query_profiles(filters)
        
        # Apply limit
        if len(profiles_data) > limit:
            profiles_data = profiles_data.head(limit)
        
        return [ProfileData(**row) for _, row in profiles_data.iterrows()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Natural language query endpoint
@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    try:
        print(f"Received query: {request.query}")
        result = rag.process_query(request.query)
        print(f"Result: {result}")
        return QueryResponse(**result)
    except Exception as e:
        print(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Generate sample data
@app.post("/api/generate-data")
async def generate_sample_data(
    num_floats: int = Query(20, description="Number of floats to generate"),
    days_back: int = Query(180, description="Days of data to generate")
):
    try:
        generator = ARGODataGenerator(num_floats=num_floats, days_back=days_back)
        floats_data, profiles_data = generator.generate_all_data()
        
        # Insert into database
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
        for float_data in floats_data:
            profile_summary = db.get_profile_summary(float_data['float_id'])
            vector_db.add_float_data(float_data, profile_summary)
        
        vector_db.save_index()
        
        return {
            "message": "Sample data generated successfully",
            "floats_generated": len(floats_data),
            "profiles_generated": len(profiles_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get float summary
@app.get("/api/floats/{float_id}/summary")
async def get_float_summary(float_id: str):
    try:
        summary = db.get_profile_summary(float_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Search similar floats
@app.get("/api/search-similar")
async def search_similar_floats(
    query: str = Query(..., description="Search query"),
    k: int = Query(5, description="Number of results")
):
    try:
        results = vector_db.search_similar(query, k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get floats by location
@app.get("/api/floats/near")
async def get_floats_near_location(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius: float = Query(1.0, description="Radius in degrees")
):
    try:
        results = vector_db.get_float_by_location(lat, lon, radius)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Export data
@app.get("/api/export")
async def export_data(
    format: str = Query("json", description="Export format (json, csv)"),
    start_date: Optional[str] = Query(None, description="Start date"),
    end_date: Optional[str] = Query(None, description="End date"),
    parameters: Optional[str] = Query(None, description="Comma-separated parameters")
):
    try:
        filters = {}
        if start_date and end_date:
            filters['date_range'] = (start_date, end_date)
        
        data = db.query_profiles(filters)
        
        if parameters:
            param_list = [p.strip() for p in parameters.split(',')]
            columns = ['profile_id', 'float_id', 'timestamp', 'latitude', 'longitude', 'depth'] + param_list
            available_columns = [col for col in columns if col in data.columns]
            data = data[available_columns]
        
        if format.lower() == "csv":
            csv_data = data.to_csv(index=False)
            return {"data": csv_data, "format": "csv"}
        else:
            return {"data": data.to_dict('records'), "format": "json"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Serve the main HTML file
@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
