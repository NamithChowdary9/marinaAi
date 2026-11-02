"""Weather Agent — monitors weather APIs and predicts storms using Gemini/OpenAI."""

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from typing import Optional
import json

from services.weather.weather_service import WeatherService
from agents.maritime_gpt.maritime_gpt_agent import _build_llm, _is_key_configured

SYSTEM_PROMPT = """You are the MarineAI Weather Agent.
Analyze real-time weather data, identify storm formations, and provide maritime safety warnings.
Always respond in valid JSON format."""


class WeatherAgent:
    def __init__(self):
        self._llm = _build_llm(temperature=0.2) if _is_key_configured() else None
        self.weather_service = WeatherService()

    async def analyze(self, query: str, location: Optional[dict] = None) -> dict:
        try:
            raw = (
                await self.weather_service.get_weather(lat=location["lat"], lon=location["lon"])
                if location
                else await self.weather_service.get_global_maritime_weather()
            )

            if self._llm is None:
                return {"raw_weather": raw, "agent_recommendation": "Configure an AI key for analysis."}

            prompt = f"""Analyze this weather data and answer: "{query}"
Data: {json.dumps(raw, default=str)[:2000]}

Return JSON:
{{"summary": string, "conditions": {{"wind_speed_kmh": number, "wave_height_m": number, "storm_risk": string}},
"warnings": [string], "forecast_6h": string, "forecast_24h": string, "agent_recommendation": string}}"""

            resp = await self._llm.ainvoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
            try:
                # Strip markdown fences if Gemini adds them
                content = resp.content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                return json.loads(content.strip())
            except Exception:
                return {"summary": resp.content, "raw_weather": raw}
        except Exception as e:
            logger.error(f"WeatherAgent: {e}")
            return {"error": str(e)}
