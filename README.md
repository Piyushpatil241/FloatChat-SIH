# ARGO AI Ocean Data Explorer

An AI-powered conversational system for exploring ARGO float oceanographic data using natural language queries and interactive visualizations.

## Features

- **Natural Language Queries**: Ask questions about ocean data in plain English
- **Interactive Dashboard**: Streamlit-based web interface with maps and visualizations
- **Vector Database**: FAISS/ChromaDB for semantic search and retrieval
- **RAG Pipeline**: Retrieval-Augmented Generation with LLM integration
- **Data Export**: Export data in CSV, JSON, and simulated NetCDF formats
- **Geospatial Visualization**: Interactive maps showing ARGO float locations
- **Profile Analysis**: Depth-time plots and parameter comparisons

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database settings
   ```

4. Set up your Groq API key:
   ```bash
   export GROQ_API_KEY="your_groq_api_key_here"
   # Or add it to your .env file
   ```

## Quick Start

### 1. Set up the database with sample data
```bash
python main.py --setup --floats 20 --days 180
```

### 2. Launch the interactive dashboard
```bash
python main.py --dashboard
```

### 3. Test the RAG system
```bash
python main.py --test
```

### 4. Run in interactive mode
```bash
python main.py --interactive
```

### 5. Test Groq integration
```bash
python test_groq.py
```

### 6. Start FastAPI backend with HTML frontend
```bash
python main.py --backend
# or
python start_backend.py
```

### 7. Test FastAPI backend
```bash
python main.py --test-backend
# or
python test_backend.py
```

## Usage Examples

### Natural Language Queries
- "Show me temperature profiles near the equator in March 2023"
- "Compare salinity in the Arabian Sea for the last 6 months"
- "What are the nearest ARGO floats to 10°N, 70°E?"
- "Show me oxygen data from active floats"

### Dashboard Features

#### Streamlit Dashboard
- **Data Overview**: Statistics and recent data tables
- **Interactive Map**: Geographic visualization of ARGO floats
- **Profile Analysis**: Depth profiles and parameter comparisons
- **AI Chat Assistant**: Natural language query interface
- **Data Export**: Download data in various formats

#### HTML/CSS/JS Frontend (FastAPI)
- **Modern Web Interface**: Responsive design with beautiful UI
- **Interactive Dashboard**: Real-time statistics and data management
- **Interactive Map**: Leaflet-based map with ARGO float locations
- **Data Analysis**: Plotly-powered charts and visualizations
- **AI Chat Interface**: Real-time chat with Groq-powered responses
- **RESTful API**: Complete API for data access and manipulation

## Architecture

### Components
1. **Data Generator**: Creates realistic dummy ARGO data
2. **Database Layer**: SQLite/PostgreSQL for structured data storage
3. **Vector Database**: FAISS/ChromaDB for semantic search
4. **RAG Pipeline**: Natural language processing and query generation
5. **Dashboard**: Streamlit web interface
6. **Export System**: Data export in multiple formats

### Data Flow
```
User Query → RAG Pipeline → Vector Search + SQL Query → LLM Response → Dashboard
```

## Configuration

### Environment Variables
- `GROQ_API_KEY`: Groq API key for LLM integration (recommended)
- `OPENAI_API_KEY`: OpenAI API key for LLM integration (alternative)
- `DATABASE_URL`: Database connection string
- `VECTOR_DB_PATH`: Path for FAISS vector database
- `CHROMA_PERSIST_DIRECTORY`: Path for ChromaDB storage

### Database Schema
- **argo_floats**: Float metadata (ID, location, status, etc.)
- **argo_profiles**: Profile data (depth, parameters, timestamps)

## API Reference

### Main Classes
- `ARGODataGenerator`: Generates realistic dummy data
- `ARGODatabase`: Database operations and queries
- `ARGOVectorDB`: Vector database for semantic search
- `ARGORAGPipeline`: RAG system for natural language processing

### Key Methods
- `process_query(query)`: Process natural language queries
- `query_profiles(filters)`: Query profile data with filters
- `search_similar(query, k)`: Find similar floats using vector search

## Extending the System

### Adding New Parameters
1. Update `ARGO_PARAMETERS` in `config.py`
2. Add parameter to database schema in `database.py`
3. Update data generator in `data_generator.py`

### Adding New Query Types
1. Add patterns to `query_patterns` in `rag_pipeline.py`
2. Update `parse_query()` method
3. Add corresponding SQL generation logic

### Adding New Visualizations
1. Create new functions in `dashboard.py`
2. Add new page to the sidebar navigation
3. Implement visualization logic using Plotly/Folium

## Future Enhancements

- Real NetCDF data integration
- Additional oceanographic parameters
- Machine learning models for data prediction
- Real-time data updates
- Multi-language support
- Advanced geospatial analysis

## Troubleshooting

### Common Issues
1. **Database errors**: Ensure database file permissions
2. **Vector DB errors**: Check FAISS/ChromaDB installation
3. **LLM errors**: Verify OpenAI API key configuration
4. **Memory issues**: Reduce number of floats or data range

### Debug Mode
Set `DEBUG=True` in `config.py` for detailed error messages.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ARGO Program for oceanographic data standards
- OpenAI for LLM capabilities
- Streamlit for dashboard framework
- Plotly and Folium for visualizations
