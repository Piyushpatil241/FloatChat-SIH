"""
Streamlit dashboard for ARGO data visualization and interaction.
Provides geospatial visualizations, profile plots, and chatbot interface.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import json

from database import ARGODatabase
from vector_db import ARGOVectorDB
from rag_pipeline import ARGORAGPipeline
from data_generator import ARGODataGenerator

# Page configuration
st.set_page_config(
    page_title="ARGO AI Ocean Data Explorer",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }
    .bot-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_systems():
    """Initialize database, vector DB, and RAG pipeline."""
    try:
        db = ARGODatabase()
        vector_db = ARGOVectorDB()
        rag = ARGORAGPipeline(db, vector_db)
        return db, vector_db, rag
    except Exception as e:
        st.error(f"Error initializing systems: {e}")
        return None, None, None

def create_argo_map(data: pd.DataFrame, center_lat: float = 0, center_lon: float = 60):
    """Create an interactive map of ARGO floats."""
    if data.empty:
        return folium.Map(location=[center_lat, center_lon], zoom_start=3)
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=4)
    
    # Add float locations
    for _, row in data.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
            # Color based on status
            color = 'green' if row.get('status') == 'active' else 'red'
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=5,
                popup=f"Float: {row['float_id']}<br>Status: {row.get('status', 'Unknown')}<br>Lat: {row['latitude']:.2f}, Lon: {row['longitude']:.2f}",
                color=color,
                fill=True,
                fillColor=color
            ).add_to(m)
    
    return m

def create_profile_plot(data: pd.DataFrame, parameter: str = 'temperature'):
    """Create depth profile plot."""
    if data.empty or parameter not in data.columns:
        return go.Figure()
    
    # Group by profile and create traces
    fig = go.Figure()
    
    for profile_id in data['profile_id'].unique()[:10]:  # Limit to 10 profiles for clarity
        profile_data = data[data['profile_id'] == profile_id]
        profile_data = profile_data.sort_values('depth')
        
        if parameter in profile_data.columns:
            values = profile_data[parameter].dropna()
            depths = profile_data['depth'][values.index]
            
            if not values.empty:
                fig.add_trace(go.Scatter(
                    x=values,
                    y=depths,
                    mode='lines+markers',
                    name=f"Profile {profile_id}",
                    line=dict(width=2),
                    marker=dict(size=4)
                ))
    
    fig.update_layout(
        title=f"{parameter.title()} vs Depth",
        xaxis_title=parameter.title(),
        yaxis_title="Depth (m)",
        yaxis=dict(autorange="reversed"),  # Depth increases downward
        height=500
    )
    
    return fig

def create_parameter_comparison(data: pd.DataFrame, parameters: list):
    """Create comparison plot for multiple parameters."""
    if data.empty or not parameters:
        return go.Figure()
    
    fig = make_subplots(
        rows=1, cols=len(parameters),
        subplot_titles=parameters,
        horizontal_spacing=0.1
    )
    
    for i, param in enumerate(parameters):
        if param in data.columns:
            values = data[param].dropna()
            if not values.empty:
                fig.add_trace(
                    go.Histogram(x=values, name=param, nbinsx=30),
                    row=1, col=i+1
                )
    
    fig.update_layout(
        title="Parameter Distributions",
        height=400,
        showlegend=False
    )
    
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">🌊 ARGO AI Ocean Data Explorer</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Initialize systems
    db, vector_db, rag = initialize_systems()
    
    if db is None:
        st.error("Failed to initialize systems. Please check your configuration.")
        return
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "Data Overview", "Interactive Map", "Profile Analysis", "AI Chat Assistant", "Data Export"
    ])
    
    # Data Overview Page
    if page == "Data Overview":
        st.header("Data Overview")
        
        # Generate sample data if needed
        if st.button("Generate Sample Data"):
            with st.spinner("Generating sample ARGO data..."):
                generator = ARGODataGenerator(num_floats=20, days_back=180)
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
                st.success("Sample data generated and loaded successfully!")
        
        # Display statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            float_count = len(db.query_floats())
            st.metric("Total Floats", float_count)
        
        with col2:
            profile_count = len(db.query_profiles())
            st.metric("Total Profiles", profile_count)
        
        with col3:
            active_floats = len(db.query_floats({'status': 'active'}))
            st.metric("Active Floats", active_floats)
        
        with col4:
            if profile_count > 0:
                latest_profile = db.query_profiles().sort_values('timestamp', ascending=False).iloc[0]
                st.metric("Latest Data", latest_profile['timestamp'].strftime('%Y-%m-%d'))
        
        # Display recent data
        st.subheader("Recent Data")
        recent_data = db.query_profiles().sort_values('timestamp', ascending=False).head(100)
        st.dataframe(recent_data[['profile_id', 'float_id', 'timestamp', 'latitude', 'longitude', 'depth', 'temperature', 'salinity']])
    
    # Interactive Map Page
    elif page == "Interactive Map":
        st.header(" Interactive Map")
        
        # Get float data
        float_data = db.query_floats()
        
        if not float_data.empty:
            # Map controls
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.subheader("Map Controls")
                
                # Filter by status
                status_filter = st.selectbox("Filter by Status", ["All", "active", "inactive", "maintenance"])
                if status_filter != "All":
                    float_data = float_data[float_data['status'] == status_filter]
                
                # Filter by institution
                institutions = ["All"] + list(float_data['institution'].unique())
                institution_filter = st.selectbox("Filter by Institution", institutions)
                if institution_filter != "All":
                    float_data = float_data[float_data['institution'] == institution_filter]
                
                st.write(f"Showing {len(float_data)} floats")
            
            with col2:
                # Create and display map
                m = create_argo_map(float_data)
                st_folium(m, width=700, height=500)
        else:
            st.warning("No float data available. Please generate sample data first.")
    
    # Profile Analysis Page
    elif page == "Profile Analysis":
        st.header(" Profile Analysis")
        
        # Get profile data
        profile_data = db.query_profiles()
        
        if not profile_data.empty:
            # Analysis controls
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("Analysis Controls")
                
                # Select parameter
                parameters = ['temperature', 'salinity', 'pressure', 'oxygen', 'nitrate', 'chlorophyll']
                selected_param = st.selectbox("Select Parameter", parameters)
                
                # Filter by depth range
                depth_range = st.slider("Depth Range (m)", 0, 2000, (0, 1000))
                filtered_data = profile_data[
                    (profile_data['depth'] >= depth_range[0]) & 
                    (profile_data['depth'] <= depth_range[1])
                ]
                
                # Filter by time range
                if not profile_data.empty:
                    min_date = profile_data['timestamp'].min()
                    max_date = profile_data['timestamp'].max()
                    date_range = st.date_input(
                        "Date Range",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                    
                    if len(date_range) == 2:
                        filtered_data = filtered_data[
                            (filtered_data['timestamp'].dt.date >= date_range[0]) &
                            (filtered_data['timestamp'].dt.date <= date_range[1])
                        ]
            
            with col2:
                # Create profile plot
                if not filtered_data.empty:
                    fig = create_profile_plot(filtered_data, selected_param)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No data available for the selected filters.")
            
            # Parameter comparison
            st.subheader("Parameter Comparison")
            comparison_params = st.multiselect(
                "Select Parameters for Comparison",
                parameters,
                default=['temperature', 'salinity']
            )
            
            if comparison_params:
                fig = create_parameter_comparison(filtered_data, comparison_params)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No profile data available. Please generate sample data first.")
    
    # AI Chat Assistant Page
    elif page == "AI Chat Assistant":
        st.header(" AI Chat Assistant")
        
        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Chat interface
        st.subheader("Ask questions about ARGO data")
        st.markdown("""
        **Example queries:**
        - "Show me temperature profiles near the equator in March 2023"
        - "Compare salinity in the Arabian Sea for the last 6 months"
        - "What are the nearest ARGO floats to 10°N, 70°E?"
        - "Show me oxygen data from active floats"
        """)
        
        # Chat input
        user_input = st.text_input("Enter your question:", key="chat_input")
        
        if st.button("Send") and user_input:
            with st.spinner("Processing your query..."):
                # Process query
                result = rag.process_query(user_input)
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "user": user_input,
                    "bot": result['response'],
                    "data_summary": result['data_summary']
                })
        
        # Display chat history
        for i, chat in enumerate(st.session_state.chat_history):
            st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {chat["user"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-message bot-message"><strong>Assistant:</strong> {chat["bot"]}</div>', unsafe_allow_html=True)
            
            # Show data summary if available
            if chat["data_summary"]["total_records"] > 0:
                with st.expander("View Data Summary"):
                    st.json(chat["data_summary"])
        
        # Clear chat history
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Data Export Page
    elif page == "Data Export":
        st.header(" Data Export")
        
        # Export controls
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Export Options")
            
            export_format = st.selectbox("Export Format", ["CSV", "JSON", "NetCDF (Simulated)"])
            
            # Data filters
            st.subheader("Data Filters")
            
            # Time range
            if not db.query_profiles().empty:
                min_date = db.query_profiles()['timestamp'].min()
                max_date = db.query_profiles()['timestamp'].max()
                date_range = st.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
            
            # Geographic bounds
            lat_range = st.slider("Latitude Range", -90.0, 90.0, (-30.0, 30.0))
            lon_range = st.slider("Longitude Range", -180.0, 180.0, (20.0, 120.0))
            
            # Parameters
            parameters = st.multiselect(
                "Select Parameters",
                ['temperature', 'salinity', 'pressure', 'oxygen', 'nitrate', 'chlorophyll', 'backscatter'],
                default=['temperature', 'salinity']
            )
        
        with col2:
            st.subheader("Export Preview")
            
            if st.button("Generate Export"):
                # Apply filters
                filters = {}
                if len(date_range) == 2:
                    filters['date_range'] = (date_range[0], date_range[1])
                filters['lat_range'] = lat_range
                filters['lon_range'] = lon_range
                
                # Get filtered data
                data = db.query_profiles(filters)
                
                if not data.empty:
                    # Select only requested parameters
                    columns = ['profile_id', 'float_id', 'timestamp', 'latitude', 'longitude', 'depth'] + parameters
                    available_columns = [col for col in columns if col in data.columns]
                    export_data = data[available_columns]
                    
                    st.success(f"Export ready: {len(export_data)} records")
                    st.dataframe(export_data.head(10))
                    
                    # Download button
                    if export_format == "CSV":
                        csv = export_data.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"argo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    elif export_format == "JSON":
                        json_data = export_data.to_json(orient='records', date_format='iso')
                        st.download_button(
                            label="Download JSON",
                            data=json_data,
                            file_name=f"argo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    elif export_format == "NetCDF (Simulated)":
                        st.info("NetCDF export simulation - in a real implementation, this would generate NetCDF files")
                else:
                    st.warning("No data available for the selected filters.")

if __name__ == "__main__":
    main()
