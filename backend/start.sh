#!/bin/bash
# ============================================================
# MarineAI — Quick Start Script
# ============================================================
set -e

echo "🌊 Starting MarineAI — Agentic Maritime Intelligence Platform"
echo "─────────────────────────────────────────────────────────────"

# Check .env
if [ ! -f backend/.env ]; then
    echo "⚠  backend/.env not found — copying from .env.example"
    cp backend/.env.example backend/.env
    echo "   → Edit backend/.env and add your API keys before continuing"
fi

# Check frontend .env.local
if [ ! -f frontend/.env.local ]; then
    echo "⚠  frontend/.env.local not found — copying from example"
    cp frontend/.env.local.example frontend/.env.local
    echo "   → Add your Mapbox token to frontend/.env.local"
fi

echo ""
echo "Starting services..."
echo ""

# Terminal 1: Backend
echo "Backend: http://localhost:8000"
echo "API Docs: http://localhost:8000/api/docs"
echo ""

# Terminal 2: Frontend
echo "Frontend: http://localhost:3100"
echo ""
echo "─────────────────────────────────────────────────────────────"
echo "Run these commands in separate terminals:"
echo ""
echo "  Terminal 1 (Backend):"
echo "    cd backend"
echo "    python -m venv venv && source venv/bin/activate"
echo "    pip install -r requirements.txt"
echo "    uvicorn main:app --reload"
echo ""
echo "  Terminal 2 (Frontend):"
echo "    cd frontend"
echo "    npm install"
echo "    npm run dev"
echo ""
echo "  Optional — Train ML models:"
echo "    python ml_models/wave_prediction/train_wave_model.py"
echo "    python ml_models/storm_prediction/train_storm_model.py"
echo ""
echo "─────────────────────────────────────────────────────────────"
echo "🔑 Required API Keys (add to backend/.env):"
echo "   OPENAI_API_KEY     — https://platform.openai.com"
echo "   OPENWEATHER_API_KEY — https://openweathermap.org/api"
echo "   AISSTREAM_API_KEY  — https://aisstream.io (free)"
echo "   (Open-Meteo: no key needed)"
echo ""
echo "🗺  Mapbox Token (add to frontend/.env.local):"
echo "   NEXT_PUBLIC_MAPBOX_TOKEN — https://mapbox.com (free)"
echo "─────────────────────────────────────────────────────────────"
