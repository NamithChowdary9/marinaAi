"""Ship Agent — tracks vessels and detects anomalies using Gemini/OpenAI."""

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from typing import Optional
import json

from services.ais.ais_service import AISService
from agents.maritime_gpt.maritime_gpt_agent import _build_llm, _is_key_configured

SYSTEM_PROMPT = """You are the MarineAI Ship Agent.
Track vessel movements, identify anomalies, and monitor traffic density.
Always respond in valid JSON."""


class ShipAgent:
    def __init__(self):
        self._llm = _build_llm(temperature=0.2) if _is_key_configured() else None
        self.ais_service = AISService()

    async def analyze(self, query: str, mmsi: Optional[str] = None, location: Optional[dict] = None) -> dict:
        try:
            if mmsi:
                data = await self.ais_service.get_vessel(mmsi)
            elif location:
                data = await self.ais_service.get_vessels_in_area(lat=location["lat"], lon=location["lon"], radius_nm=100)
            else:
                data = await self.ais_service.get_global_snapshot()

            if self._llm is None:
                return {"raw_data": data}

            prompt = f"""Analyze vessel data and answer: "{query}"
Data: {json.dumps(data, default=str)[:2000]}

Return JSON:
{{"total_vessels_tracked": number,
"vessels_at_risk": [{{"mmsi": string, "name": string, "risk_reason": string, "risk_level": string}}],
"traffic_summary": {{"busiest_corridors": [string]}},
"anomalies": [string],
"agent_recommendation": string}}"""

            resp = await self._llm.ainvoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
            try:
                content = resp.content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                return json.loads(content.strip())
            except Exception:
                return {"summary": resp.content}
        except Exception as e:
            logger.error(f"ShipAgent: {e}")
            return {"error": str(e)}
