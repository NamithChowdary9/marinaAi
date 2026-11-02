"""Risk Assessment Agent — calculates maritime danger scores using Gemini/OpenAI."""

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from typing import Optional
import json

from agents.maritime_gpt.maritime_gpt_agent import _build_llm, _is_key_configured

SYSTEM_PROMPT = """You are the MarineAI Risk Agent.
Calculate maritime danger scores (0-100): 0-25 SAFE, 26-50 LOW, 51-75 HIGH, 76-100 CRITICAL.
Always respond in valid JSON."""


class RiskAgent:
    def __init__(self):
        self._llm = _build_llm(temperature=0.2) if _is_key_configured() else None

    async def analyze(self, query: str, weather=None, wave=None, ship=None, location=None) -> dict:
        try:
            # Rule-based fallback
            if self._llm is None:
                wh = 0.0
                if isinstance(wave, dict):
                    wh = (wave.get("current_waves") or {}).get("height_m") or wave.get("wave_height_m", 0)
                score = min(100, wh * 12)
                level = "safe" if score < 25 else "low" if score < 50 else "high" if score < 75 else "critical"
                return {"overall_risk_score": round(score, 1), "risk_level": level,
                        "recommendations": ["Add GEMINI_API_KEY for detailed AI risk analysis."]}

            context = {"weather": weather, "waves": wave, "vessels": ship, "location": location}
            prompt = f"""Risk assessment for: "{query}"
Context: {json.dumps(context, default=str)[:2000]}

Return JSON:
{{"overall_risk_score": number, "risk_level": string, "risk_color": string,
"risk_breakdown": {{"weather_risk": number, "wave_risk": number, "collision_risk": number}},
"danger_zones": [{{"region": string, "risk_score": number, "primary_threat": string}}],
"recommendations": [string], "agent_recommendation": string}}"""

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
            logger.error(f"RiskAgent: {e}")
            return {"error": str(e)}
