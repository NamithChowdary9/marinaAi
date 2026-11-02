"""Wave Agent — analyzes ocean wave data using Gemini/OpenAI + ML models."""

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from typing import Optional
import json

from services.ocean.ocean_service import OceanService
from ml.inference.wave_predictor import WavePredictor
from agents.maritime_gpt.maritime_gpt_agent import _build_llm, _is_key_configured

SYSTEM_PROMPT = """You are the MarineAI Wave Agent.
Analyze wave data and classify danger levels: 🟢 Safe (<2m), 🟡 Moderate (2-4m), 🔴 Dangerous (>4m).
Always respond in valid JSON."""


class WaveAgent:
    def __init__(self):
        self._llm = _build_llm(temperature=0.2) if _is_key_configured() else None
        self.ocean_service = OceanService()
        self.wave_predictor = WavePredictor()

    async def analyze(self, query: str, location: Optional[dict] = None, weather_context: Optional[dict] = None) -> dict:
        try:
            ocean_data = (
                await self.ocean_service.get_wave_data(lat=location["lat"], lon=location["lon"])
                if location
                else await self.ocean_service.get_global_wave_summary()
            )

            ml_predictions = {}
            try:
                wh = ocean_data.get("wave_height_m", 1.5) if isinstance(ocean_data, dict) else 1.5
                ml_predictions = self.wave_predictor.predict(
                    wind_speed=20, pressure=1013, humidity=75, temperature=25,
                    current_wave_height=wh,
                )
            except Exception:
                pass

            if self._llm is None:
                return {"ocean_data": ocean_data, "ml_predictions": ml_predictions}

            prompt = f"""Analyze wave data and answer: "{query}"
Ocean: {json.dumps(ocean_data, default=str)[:1500]}
ML: {json.dumps(ml_predictions)}

Return JSON:
{{"current_waves": {{"height_m": number, "danger_level": string, "danger_color": string}},
"predictions": {{"6h": {{"height_m": number}}, "24h": {{"height_m": number}}, "72h": {{"height_m": number}}}},
"vessel_safety": {{"large_vessels": string, "fishing_boats": string, "small_boats": string}},
"agent_recommendation": string}}"""

            resp = await self._llm.ainvoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
            try:
                content = resp.content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                result = json.loads(content.strip())
                result["ml_predictions"] = ml_predictions
                return result
            except Exception:
                return {"summary": resp.content, "ml_predictions": ml_predictions}
        except Exception as e:
            logger.error(f"WaveAgent: {e}")
            return {"error": str(e)}
