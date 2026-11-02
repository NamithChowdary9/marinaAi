"""
Maritime Chat API — ChatGPT-style maritime Q&A endpoint.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from agents.maritime_gpt.maritime_gpt_agent import MaritimeGPTAgent
from agents.orchestrator.master_orchestrator import MasterOrchestrator
from services.weather.weather_service import WeatherService

router = APIRouter()
maritime_gpt = MaritimeGPTAgent()
orchestrator = MasterOrchestrator()
weather_service = WeatherService()


class ChatMessage(BaseModel):
    role: str  # user / assistant
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    location: Optional[dict] = None           # {lat, lon, name}
    vessel_mmsi: Optional[str] = None
    use_agents: bool = True                    # if True, use full multi-agent pipeline


class ChatResponse(BaseModel):
    answer: str
    agents_used: Optional[List[str]] = []
    weather_data: Optional[dict] = None
    wave_data: Optional[dict] = None
    risk_assessment: Optional[dict] = None
    route_data: Optional[dict] = None


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Maritime AI Chat endpoint.
    
    For simple questions → uses MaritimeGPT directly.
    For complex queries involving real-time data → routes through multi-agent orchestrator.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Build real-time context
    context = {}
    if request.location:
        try:
            weather = await weather_service.get_weather(
                lat=request.location["lat"],
                lon=request.location["lon"],
            )
            context["weather"] = weather
        except Exception:
            pass

    if request.use_agents:
        # Use direct maritime GPT — it has Gemini + instant fallback
        # (orchestrator causes timeouts due to sequential agent calls)
        history_dicts = [m.dict() for m in (request.history or [])]
        answer = await maritime_gpt.chat(
            message=request.message,
            history=history_dicts,
            context=context,
        )
        return ChatResponse(answer=answer, agents_used=["maritime_gpt"])
    else:
        history_dicts = [m.dict() for m in (request.history or [])]
        answer = await maritime_gpt.chat(
            message=request.message,
            history=history_dicts,
            context=context,
        )
        return ChatResponse(answer=answer, agents_used=["maritime_gpt"])


@router.post("/quick")
async def quick_chat(body: dict):
    """Quick single-turn chat without history."""
    message = body.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Message required")

    answer = await maritime_gpt.quick_answer(message)
    return {"answer": answer}
