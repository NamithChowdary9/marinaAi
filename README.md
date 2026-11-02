# 🌊 MarineAI — Agentic Maritime Intelligence Platform

> Real-time ship tracking + Ocean risk prediction + Agentic AI + ML models

---

## 🚀 What is MarineAI?

MarineAI is a fully agentic AI-powered web application that monitors global maritime activity in real time. It combines:

- 🛳 **Live Ship Tracking** via AIS data
- 🌦 **Real-time Weather Overlays**
- 🌊 **Ocean Wave & Disturbance Prediction** (ML models)
- 🤖 **Multi-Agent AI System** (LangGraph orchestration)
- 💬 **Maritime ChatGPT** (ask anything about ocean conditions)
- ⚠️ **Emergency Detection & Alerts**
- 🗺 **AI Route Optimization**

---

## 🏗 Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Mapbox GL |
| Backend | FastAPI, Python 3.11 |
| Database | PostgreSQL + TimescaleDB |
| AI/LLM | GPT-4o, LangGraph, LangChain |
| ML | PyTorch, Scikit-learn, XGBoost |
| Agents | LangGraph multi-agent orchestration |
| Real-time | WebSockets |
| Cache | Redis |

---

## 📁 Project Structure

```
marineAI/
├── frontend/          # Next.js app
├── backend/           # FastAPI server + AI agents
├── ml_models/         # ML training & inference
└── docs/              # Architecture & API docs
```

---

## ⚡ Quick Start

### 1. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Add your API keys
uvicorn main:app --reload
```

### 2. Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local   # Add your Mapbox token
npm run dev
```

The frontend runs at `http://localhost:3100`; the API and API docs run at
`http://localhost:8000` and `http://localhost:8000/api/docs` respectively.

---

## 🔑 Required API Keys

| Key | Source |
|-----|--------|
| `OPENAI_API_KEY` | https://platform.openai.com |
| `MAPBOX_TOKEN` | https://mapbox.com |
| `OPENWEATHER_API_KEY` | https://openweathermap.org/api |
| `AISSTREAM_API_KEY` | https://aisstream.io (free tier available) |
| `OPEN_METEO` | No key needed (free) |

---

## 🤖 AI Agents

| Agent | Role |
|-------|------|
| Weather Agent | Monitors weather APIs, predicts storms |
| Wave Agent | Analyzes wave data, predicts disturbances |
| Ship Agent | Tracks vessels, detects anomalies |
| Route Agent | Generates optimal safe routes |
| Risk Agent | Calculates danger scores |
| Maritime GPT | Answers natural language maritime questions |
| Orchestrator | Coordinates all agents |

---

## 🌊 ML Models

1. **Wave Prediction** — LSTM + XGBoost predicts wave height 6/24/72h ahead
2. **Storm Prediction** — Transformer model predicts storm probability
3. **Collision Prediction** — Gradient Boosting for vessel collision risk
4. **Route Recommendation** — Reinforcement Learning for optimal routing

---

## 📸 Features

- World map with live ship positions
- Click any ship → full vessel details + AI risk assessment
- Wave intensity heatmap (green/yellow/red)
- Weather overlay (wind, rain, pressure, cyclones)
- AI chat: "Is it safe to sail from Mumbai to Colombo tomorrow?"
- Danger zone alerts with autonomous agent monitoring
- Route optimizer with fuel savings estimate

---

## 🔮 Future Scope

- Satellite image analysis (oil spill, illegal fishing)
- Drone monitoring integration
- Pirate activity risk zones
- Coast Guard emergency dashboard
- Carbon emission tracking
- Digital Ocean Twin simulation

---

Built with ❤️ as an Agentic AI final-year / hackathon project.
