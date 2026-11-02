"""
Agents API — direct access to individual AI agents.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from agents.orchestrator.master_orchestrator import MasterOrchestrator

router = APIRouter()
orchestrator = MasterOrchestrator()


class AgentQuery(BaseModel):
    query: str
    location: Optional[dict] = None
    vessel_mmsi: Optional[str] = None


@router.post("/run")
async def run_orchestrator(body: AgentQuery):
    """Run the full multi-agent orchestration pipeline."""
    result = await orchestrator.run(
        query=body.query,
        location=body.location,
        vessel_mmsi=body.vessel_mmsi,
    )
    return result


@router.get("/status")
async def get_agents_status():
    """Get the status of all AI agents."""
    return {
        "agents": [
            {"name": "weather_agent", "status": "active", "description": "Monitors weather & storm prediction"},
            {"name": "wave_agent", "status": "active", "description": "Wave analysis & prediction"},
            {"name": "ship_agent", "status": "active", "description": "Vessel tracking & anomaly detection"},
            {"name": "route_agent", "status": "active", "description": "Route optimization"},
            {"name": "risk_agent", "status": "active", "description": "Danger score calculation"},
            {"name": "maritime_gpt", "status": "active", "description": "Natural language Q&A"},
            {"name": "orchestrator", "status": "active", "description": "Coordinates all agents"},
        ],
        "framework": "LangGraph",
        "llm": "GPT-4o",
        "total_agents": 7,
    }
