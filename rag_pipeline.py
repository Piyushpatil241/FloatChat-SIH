"""
RAG (Retrieval-Augmented Generation) pipeline for ARGO data.
Integrates with LLMs to answer natural language queries about oceanographic data.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import json
import re
from datetime import datetime, timedelta
from database import ARGODatabase
from vector_db import ARGOVectorDB
from config import GROQ_API_KEY

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("Groq not available, using mock responses")

class ARGORAGPipeline:
    def __init__(self, database: ARGODatabase, vector_db: ARGOVectorDB):
        self.db = database
        self.vector_db = vector_db
        self.groq_client = None
        
        if GROQ_AVAILABLE and GROQ_API_KEY:
            self.groq_client = Groq(api_key=GROQ_API_KEY)
        
        # Query patterns for different types of questions
        self.query_patterns = {
            'location': r'(near|around|close to|at|in)\s+([\d.-]+)\s*,\s*([\d.-]+)',
            'region': r'(equator|poles?|tropical|arctic|antarctic|indian ocean|pacific|atlantic)',
            'parameter': r'(temperature|salinity|pressure|oxygen|nitrate|chlorophyll|backscatter)',
            'time': r'(march|april|may|june|july|august|september|october|november|december|january|february|\d{4}|\d{1,2}\s+months?)',
            'comparison': r'(compare|comparison|vs|versus|difference)',
            'profile': r'(profile|profiles|depth|vertical)',
            'float': r'(float|floats|argo)'
        }
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse natural language query to extract structured information."""
        query_lower = query.lower()
        parsed = {
            'original_query': query,
            'intent': 'unknown',
            'parameters': [],
            'location': None,
            'time_range': None,
            'region': None,
            'comparison': False,
            'profile_request': False
        }
        
        # Extract parameters
        for param in ['temperature', 'salinity', 'pressure', 'oxygen', 'nitrate', 'chlorophyll', 'backscatter']:
            if param in query_lower:
                parsed['parameters'].append(param)
        
        # Extract location coordinates
        location_match = re.search(self.query_patterns['location'], query_lower)
        if location_match:
            parsed['location'] = {
                'lat': float(location_match.group(2)),
                'lon': float(location_match.group(3))
            }
        
        # Extract region
        for region in ['equator', 'poles', 'tropical', 'arctic', 'antarctic', 'indian ocean', 'pacific', 'atlantic']:
            if region in query_lower:
                parsed['region'] = region
                break
        
        # Extract time information
        time_match = re.search(r'(\d{4})', query)
        if time_match:
            year = int(time_match.group(1))
            parsed['time_range'] = {
                'start': datetime(year, 1, 1),
                'end': datetime(year, 12, 31)
            }
        
        # Check for month
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        for month_name, month_num in months.items():
            if month_name in query_lower:
                if parsed['time_range']:
                    parsed['time_range']['start'] = parsed['time_range']['start'].replace(month=month_num)
                    parsed['time_range']['end'] = parsed['time_range']['end'].replace(month=month_num)
                else:
                    current_year = datetime.now().year
                    parsed['time_range'] = {
                        'start': datetime(current_year, month_num, 1),
                        'end': datetime(current_year, month_num, 28)
                    }
        
        # Check for comparison
        if any(word in query_lower for word in ['compare', 'comparison', 'vs', 'versus', 'difference']):
            parsed['comparison'] = True
        
        # Check for profile request
        if any(word in query_lower for word in ['profile', 'profiles', 'depth', 'vertical']):
            parsed['profile_request'] = True
        
        # Determine intent
        if parsed['location'] or parsed['region']:
            if parsed['parameters']:
                parsed['intent'] = 'parameter_query'
            else:
                parsed['intent'] = 'location_query'
        elif parsed['parameters']:
            parsed['intent'] = 'parameter_query'
        elif parsed['comparison']:
            parsed['intent'] = 'comparison_query'
        else:
            parsed['intent'] = 'general_query'
        
        return parsed
    
    def generate_sql_query(self, parsed_query: Dict[str, Any]) -> str:
        """Generate SQL query based on parsed natural language query."""
        base_query = "SELECT * FROM argo_profiles WHERE 1=1"
        conditions = []
        
        # Add parameter filters
        if parsed_query['parameters']:
            param_conditions = []
            for param in parsed_query['parameters']:
                param_conditions.append(f"{param} IS NOT NULL")
            conditions.append(f"({' AND '.join(param_conditions)})")
        
        # Add location filters
        if parsed_query['location']:
            lat, lon = parsed_query['location']['lat'], parsed_query['location']['lon']
            radius = 1.0  # degrees
            conditions.append(f"latitude BETWEEN {lat - radius} AND {lat + radius}")
            conditions.append(f"longitude BETWEEN {lon - radius} AND {lon + radius}")
        elif parsed_query['region']:
            region_bounds = self._get_region_bounds(parsed_query['region'])
            if region_bounds:
                conditions.append(f"latitude BETWEEN {region_bounds['min_lat']} AND {region_bounds['max_lat']}")
                conditions.append(f"longitude BETWEEN {region_bounds['min_lon']} AND {region_bounds['max_lon']}")
        
        # Add time filters
        if parsed_query['time_range']:
            start_date = parsed_query['time_range']['start'].strftime('%Y-%m-%d')
            end_date = parsed_query['time_range']['end'].strftime('%Y-%m-%d')
            conditions.append(f"timestamp BETWEEN '{start_date}' AND '{end_date}'")
        
        # Add depth filter for profile requests
        if parsed_query['profile_request']:
            conditions.append("depth <= 1000")  # Focus on upper ocean
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
        
        # Add ordering
        if parsed_query['profile_request']:
            base_query += " ORDER BY float_id, timestamp, depth"
        else:
            base_query += " ORDER BY timestamp DESC"
        
        return base_query
    
    def _get_region_bounds(self, region: str) -> Optional[Dict[str, float]]:
        """Get geographic bounds for named regions."""
        region_bounds = {
            'equator': {'min_lat': -5, 'max_lat': 5, 'min_lon': -180, 'max_lon': 180},
            'tropical': {'min_lat': -23.5, 'max_lat': 23.5, 'min_lon': -180, 'max_lon': 180},
            'indian ocean': {'min_lat': -30, 'max_lat': 30, 'min_lon': 20, 'max_lon': 120},
            'pacific': {'min_lat': -60, 'max_lat': 60, 'min_lon': 120, 'max_lon': -60},
            'atlantic': {'min_lat': -60, 'max_lat': 60, 'min_lon': -80, 'max_lon': 20}
        }
        return region_bounds.get(region.lower())
    
    def retrieve_relevant_data(self, parsed_query: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Retrieve relevant data using both SQL and vector search."""
        # Get data from SQL database
        sql_query = self.generate_sql_query(parsed_query)
        sql_data = self.db.execute_sql(sql_query)
        
        # Get similar floats from vector database
        vector_results = []
        if parsed_query['intent'] in ['general_query', 'location_query']:
            vector_results = self.vector_db.search_similar(parsed_query['original_query'], k=5)
        
        return sql_data, vector_results
    
    def generate_response(self, parsed_query: Dict[str, Any], sql_data: pd.DataFrame, 
                        vector_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response with LLM text and chart-ready data."""
        # Prepare context for LLM
        context_parts = []

        if not sql_data.empty:
            context_parts.append(f"Found {len(sql_data)} data points:")
            if parsed_query['parameters']:
                for param in parsed_query['parameters']:
                    if param in sql_data.columns:
                        values = sql_data[param].dropna()
                        if not values.empty:
                            context_parts.append(f"- {param}: {values.min():.2f} to {values.max():.2f} (mean: {values.mean():.2f})")
            if 'latitude' in sql_data.columns and 'longitude' in sql_data.columns:
                context_parts.append(f"- Geographic range: {sql_data['latitude'].min():.2f}°N to {sql_data['latitude'].max():.2f}°N, "
                                    f"{sql_data['longitude'].min():.2f}°E to {sql_data['longitude'].max():.2f}°E")
            if 'timestamp' in sql_data.columns:
                context_parts.append(f"- Time range: {sql_data['timestamp'].min()} to {sql_data['timestamp'].max()}")

        if vector_results:
            context_parts.append("Relevant ARGO floats:")
            for result in vector_results[:3]:
                context_parts.append(f"- {result['float_id']}: {result['text_summary']}")

        context_text = "\n".join(context_parts)

        # Generate LLM response
        response_text = ""
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "You are an oceanographic data assistant. Provide clear scientific explanations of ARGO float data."},
                        {"role": "user", "content": f"Query: {parsed_query['original_query']}\n\nData context:\n{context_text}"}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                response_text = response.choices[0].message.content
            except Exception as e:
                print(f"Error calling Groq API: {e}")
                response_text = None

        if not response_text:
            response_text = self._generate_fallback_response(parsed_query, sql_data, vector_results)

        # Prepare chart-ready data
        charts = []
        if not sql_data.empty and 'depth' in sql_data.columns:
            for param in parsed_query['parameters']:
                if param in sql_data.columns:
                    datasets = []
                    for float_id, group in sql_data.groupby('float_id'):
                        group_sorted = group.sort_values('depth')
                        datasets.append({
                            "label": float_id,
                            "data": group_sorted[param].tolist(),
                            "borderColor": "rgba(75, 192, 192, 1)",
                            "fill": False
                        })
                    chart = {
                        "type": "line",
                        "data": {
                            "labels": sorted(sql_data['depth'].unique().tolist()),
                            "datasets": datasets
                        },
                        "options": {
                            "responsive": True,
                            "plugins": {"legend": {"position": "top"}},
                            "scales": {"y": {"reverse": True, "title": {"display": True, "text": "Depth (m)"}}}
                        }
                    }
                    charts.append(chart)

        return {
            "response_text": response_text,
            "charts": charts
        }

    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a natural language query safely and return structured JSON for frontend."""
        try:
            parsed_query = self.parse_query(query)
            
            # Retrieve relevant data
            sql_data, vector_results = self.retrieve_relevant_data(parsed_query)
            
            # Ensure sql_data is a DataFrame
            if sql_data is None:
                import pandas as pd
                sql_data = pd.DataFrame()
            
            # Ensure vector_results is a list
            if vector_results is None:
                vector_results = []
            
            # Generate LLM and chart data
            llm_and_chart_data = self.generate_response(parsed_query, sql_data, vector_results)
            response_text = llm_and_chart_data.get('response_text', '')
            charts = llm_and_chart_data.get('charts', [])
            
            # Prepare data summary safely
            data_summary = {
                'total_records': len(sql_data),
                'parameters_found': [col for col in sql_data.columns if col in [
                    'temperature', 'salinity', 'pressure', 'oxygen', 'nitrate',
                    'chlorophyll', 'backscatter'
                ]] if not sql_data.empty else [],
                'geographic_bounds': None
            }
            
            if not sql_data.empty:
                data_summary['geographic_bounds'] = {
                    'min_lat': sql_data['latitude'].min(),
                    'max_lat': sql_data['latitude'].max(),
                    'min_lon': sql_data['longitude'].min(),
                    'max_lon': sql_data['longitude'].max()
                }
            
            # Return a clean structure matching QueryResponse
            return {
                'query': query,
                'response': response_text,
                'data_summary': data_summary,
                'data': sql_data.to_dict('records'),
                'vector_results': vector_results
            }
        
        except Exception as e:
            # Fallback in case something unexpected happens
            print(f"Error in process_query: {e}")
            return {
                'query': query,
                'response': f"Error processing query: {e}",
                'data_summary': {'total_records': 0, 'parameters_found': [], 'geographic_bounds': None},
                'data': [],
                'vector_results': []
            }



if __name__ == "__main__":
    # Test RAG pipeline
    from database import ARGODatabase
    from vector_db import ARGOVectorDB
    
    db = ARGODatabase()
    vector_db = ARGOVectorDB()
    rag = ARGORAGPipeline(db, vector_db)
    
    
    # Test query
    #test_query = "Show me temperature profiles near the equator in March 2023"
    #result = rag.process_query(test_query)
    #print("Query:", test_query)
    #print("Response:", result['response'])
