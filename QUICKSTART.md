# 🚀 ARGO AI Ocean Data Explorer - Quick Start Guide

## 🌊 Complete System Overview

The ARGO AI system now offers **two frontend options**:

1. **Streamlit Dashboard** - Python-based interactive interface
2. **FastAPI + HTML/CSS/JS** - Modern web application with REST API

## ⚡ Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up Groq API (Optional but recommended)
```bash
python setup_groq.py
# or manually set: export GROQ_API_KEY="your_key_here"
```

### 3. Choose Your Frontend

#### Option A: Streamlit Dashboard
```bash
python main.py --setup --floats 20 --days 180
python main.py --dashboard
```
**Access:** http://localhost:8501

#### Option B: FastAPI Web Interface
```bash
python main.py --setup --floats 20 --days 180
python main.py --backend
```
**Access:** http://localhost:8000

#### Option C: Complete Demo
```bash
python demo_full_system.py
```

## 🎯 Key Features

### Both Frontends Include:
- **Interactive Maps** - Visualize ARGO float locations
- **Data Analysis** - Depth profiles and parameter comparisons
- **AI Chat** - Natural language queries powered by Groq
- **Real-time Stats** - System statistics and data overview
- **Data Export** - Download data in multiple formats

### FastAPI Frontend Additional Features:
- **Modern UI** - Responsive design with beautiful animations
- **REST API** - Complete API for data access
- **Real-time Updates** - Live data refresh
- **Mobile Friendly** - Works on all devices

## 🔧 System Architecture

```
┌─────────────────┐    ┌─────────────────┐
│  Streamlit UI   │    │   HTML/CSS/JS   │
│   (Port 8501)   │    │   (Port 8000)   │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
            ┌────────▼────────┐
            │   FastAPI       │
            │   Backend       │
            └────────┬────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼────┐  ┌────▼────┐  ┌───▼────┐
   │Database │  │Vector DB│  │Groq LLM│
   │(SQLite) │  │(FAISS)  │  │(Llama3)│
   └─────────┘  └─────────┘  └────────┘
```

## 📊 Sample Queries

Try these natural language queries in the chat interface:

- "What is ARGO data and how does it work?"
- "Show me temperature profiles near the equator"
- "Compare salinity data from different regions"
- "What are the nearest ARGO floats to 10°N, 70°E?"
- "Show me oxygen data from active floats"

## 🛠️ Development

### Backend Development
```bash
# Start with auto-reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
- Edit files in `frontend/` directory
- Changes are automatically served by FastAPI
- No build process required

### API Testing
```bash
python test_backend.py
```

## 🚨 Troubleshooting

### Common Issues:

1. **Port already in use**
   - Streamlit: Change port with `--server.port 8502`
   - FastAPI: Change port in `start_backend.py`

2. **Database errors**
   - Delete `argo_data.db` and run setup again
   - Check file permissions

3. **Groq API errors**
   - Verify API key: `python test_groq.py`
   - Check internet connection

4. **Missing dependencies**
   - Run: `pip install -r requirements.txt`
   - For specific errors, install packages individually

### Getting Help:
- Check the full README.md for detailed documentation
- Run `python demo_full_system.py` for guided setup
- View API documentation at http://localhost:8000/docs

## 🎉 Success!

Once running, you should see:
- **Streamlit**: Interactive dashboard with tabs for different features
- **FastAPI**: Modern web interface with navigation and real-time updates

Both interfaces provide the same core functionality with different user experiences. Choose the one that best fits your needs!

---

**Happy Ocean Data Exploring! 🌊🤖**
