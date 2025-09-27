"""
Database setup and management for ARGO data.
Supports both PostgreSQL and SQLite for flexibility.
"""

import pandas as pd
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from typing import List, Dict, Any
import json
from config import DATABASE_URL

Base = declarative_base()

class ARGOFloat(Base):
    __tablename__ = 'argo_floats'
    
    id = Column(Integer, primary_key=True)
    float_id = Column(String(50), unique=True, nullable=False)
    platform_type = Column(String(50))
    deployment_date = Column(DateTime)
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(String(20))
    max_pressure = Column(Integer)
    cycle_time = Column(Integer)
    institution = Column(String(100))

class ARGOProfile(Base):
    __tablename__ = 'argo_profiles'
    
    id = Column(Integer, primary_key=True)
    profile_id = Column(String(100), nullable=False)
    float_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime)
    latitude = Column(Float)
    longitude = Column(Float)
    depth = Column(Float)
    temperature = Column(Float)
    salinity = Column(Float)
    pressure = Column(Float)
    oxygen = Column(Float)
    nitrate = Column(Float)
    chlorophyll = Column(Float)
    backscatter = Column(Float)
    downwelling_irradiance = Column(Float)

class ARGODatabase:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or DATABASE_URL
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        """Create database tables."""
        Base.metadata.create_all(self.engine)
        print("Database tables created successfully.")
    
    def insert_floats(self, floats_data: List[Dict[str, Any]]):
        """Insert float metadata into database."""
        session = self.Session()
        try:
            for float_data in floats_data:
                float_obj = ARGOFloat(**float_data)
                session.add(float_obj)
            session.commit()
            print(f"Inserted {len(floats_data)} float records.")
        except Exception as e:
            session.rollback()
            print(f"Error inserting floats: {e}")
        finally:
            session.close()
    
    def insert_profiles(self, profiles_data: List[Dict[str, Any]]):
        session = self.Session()
        try:
            for profile_data in profiles_data:
                existing = session.query(ARGOProfile).filter_by(profile_id=profile_data["profile_id"]).first()
                if existing:
                    print(f"Skipping duplicate profile_id: {profile_data['profile_id']}")
                    continue
                profile_obj = ARGOProfile(**profile_data)
                session.add(profile_obj)
            session.commit()
            print(f"Inserted {len(profiles_data)} profile records (excluding duplicates).")
        except Exception as e:
            session.rollback()
            print(f"Error inserting profiles: {e}")
        finally:
            session.close()

    
    def query_floats(self, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Query float data with optional filters."""
        session = self.Session()
        try:
            query = session.query(ARGOFloat)
            
            if filters:
                if 'status' in filters:
                    query = query.filter(ARGOFloat.status == filters['status'])
                if 'institution' in filters:
                    query = query.filter(ARGOFloat.institution == filters['institution'])
                if 'lat_range' in filters:
                    min_lat, max_lat = filters['lat_range']
                    query = query.filter(ARGOFloat.latitude.between(min_lat, max_lat))
                if 'lon_range' in filters:
                    min_lon, max_lon = filters['lon_range']
                    query = query.filter(ARGOFloat.longitude.between(min_lon, max_lon))
            
            results = query.all()
            data = []
            for result in results:
                data.append({
                    'float_id': result.float_id,
                    'platform_type': result.platform_type,
                    'deployment_date': result.deployment_date,
                    'latitude': result.latitude,
                    'longitude': result.longitude,
                    'status': result.status,
                    'max_pressure': result.max_pressure,
                    'cycle_time': result.cycle_time,
                    'institution': result.institution
                })
            
            return pd.DataFrame(data)
        finally:
            session.close()
    
    def query_profiles(self, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Query profile data with optional filters."""
        session = self.Session()
        try:
            query = session.query(ARGOProfile)
            
            if filters:
                if 'float_id' in filters:
                    query = query.filter(ARGOProfile.float_id == filters['float_id'])
                if 'date_range' in filters:
                    start_date, end_date = filters['date_range']
                    query = query.filter(ARGOProfile.timestamp.between(start_date, end_date))
                if 'lat_range' in filters:
                    min_lat, max_lat = filters['lat_range']
                    query = query.filter(ARGOProfile.latitude.between(min_lat, max_lat))
                if 'lon_range' in filters:
                    min_lon, max_lon = filters['lon_range']
                    query = query.filter(ARGOProfile.longitude.between(min_lon, max_lon))
                if 'depth_range' in filters:
                    min_depth, max_depth = filters['depth_range']
                    query = query.filter(ARGOProfile.depth.between(min_depth, max_depth))
                if 'parameter' in filters:
                    param_name = filters['parameter']
                    if hasattr(ARGOProfile, param_name):
                        param_col = getattr(ARGOProfile, param_name)
                        if 'min_value' in filters:
                            query = query.filter(param_col >= filters['min_value'])
                        if 'max_value' in filters:
                            query = query.filter(param_col <= filters['max_value'])
            
            results = query.all()
            data = []
            for result in results:
                data.append({
                    'profile_id': result.profile_id,
                    'float_id': result.float_id,
                    'timestamp': result.timestamp,
                    'latitude': result.latitude,
                    'longitude': result.longitude,
                    'depth': result.depth,
                    'temperature': result.temperature,
                    'salinity': result.salinity,
                    'pressure': result.pressure,
                    'oxygen': result.oxygen,
                    'nitrate': result.nitrate,
                    'chlorophyll': result.chlorophyll,
                    'backscatter': result.backscatter,
                    'downwelling_irradiance': result.downwelling_irradiance
                })
            
            return pd.DataFrame(data)
        finally:
            session.close()
    
    def get_profile_summary(self, float_id: str = None) -> Dict[str, Any]:
        """Get summary statistics for profiles."""
        session = self.Session()
        try:
            query = session.query(ARGOProfile)
            if float_id:
                query = query.filter(ARGOProfile.float_id == float_id)
            
            results = query.all()
            
            if not results:
                return {}
            
            # Calculate statistics
            depths = [r.depth for r in results]
            temperatures = [r.temperature for r in results if r.temperature is not None]
            salinities = [r.salinity for r in results if r.salinity is not None]
            
            summary = {
                'total_profiles': len(set(r.profile_id for r in results)),
                'total_measurements': len(results),
                'depth_range': {
                    'min': min(depths),
                    'max': max(depths)
                },
                'temperature_stats': {
                    'min': min(temperatures) if temperatures else None,
                    'max': max(temperatures) if temperatures else None,
                    'mean': sum(temperatures) / len(temperatures) if temperatures else None
                },
                'salinity_stats': {
                    'min': min(salinities) if salinities else None,
                    'max': max(salinities) if salinities else None,
                    'mean': sum(salinities) / len(salinities) if salinities else None
                }
            }
            
            return summary
        finally:
            session.close()
    
    def execute_sql(self, sql_query: str) -> pd.DataFrame:
        """Execute raw SQL query and return results as DataFrame."""
        try:
            return pd.read_sql_query(sql_query, self.engine)
        except Exception as e:
            print(f"Error executing SQL query: {e}")
            return pd.DataFrame()

if __name__ == "__main__":
    # Test database setup
    db = ARGODatabase()
    print("Database setup completed successfully!")
