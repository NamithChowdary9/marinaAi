"""
Master Orchestrator Agent — coordinates all specialized maritime agents.
"""

from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
import json

from agents.weather.weather_agent import WeatherAgent
from agents.wave.wave_agent import WaveAgent
from agents.ship.ship_agent import ShipAgent
from agents.route.route_agent import RouteAgent
from agents.risk.risk_agent import RiskAgent
from agents.maritime_gpt.maritime_gpt_agent import MaritimeGPTAgent, _build_llm, _is_key_configured
from config.settings import settings


# ─── State ───────────────────────────────────────────────────────────────────

class MarineAgentState(TypedDict):
    query: str
    location: Optional[dict]
    vessel_mmsi: Optional[str]
    route_request: Optional[dict]
    weather_data: Optional[dict]
    wave_data: Optional[dict]
    ship_data: Optional[dict]
    route_data: Optional[dict]
    risk_assessment: Optional[dict]
    final_answer: Optional[str]
    messages: List[dict]
    active_agents: List[str]
    iteration: int


# ─── Orchestrator ─────────────────────────────────────────────────────────────

class MasterOrchestrator:
    def __init__(self):
        self._llm = _build_llm(temperature=0.3) if _is_key_configured() else None
        self.weather_agent = WeatherAgent()
        self.wave_agent    = WaveAgent()
        self.ship_agent    = ShipAgent()
        self.route_agent   = RouteAgent()
        self.risk_agent    = RiskAgent()
        self.maritime_gpt  = MaritimeGPTAgent()
        self.graph         = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(MarineAgentState)
        graph.add_node("router",      self._router_node)
        graph.add_node("weather",     self._weather_node)
        graph.add_node("wave",        self._wave_node)
        graph.add_node("ship",        self._ship_node)
        graph.add_node("route",       self._route_node)
        graph.add_node("risk",        self._risk_node)
        graph.add_node("synthesizer", self._synthesizer_node)
        graph.set_entry_point("router")
        graph.add_conditional_edges("router", self._decide_agents, {
            "weather": "weather", "wave": "wave", "ship": "ship",
            "route": "route", "risk": "risk", "synthesize": "synthesizer",
        })
        for node in ["weather", "wave", "ship", "route", "risk"]:
            graph.add_conditional_edges(node, self._next_agent_or_synthesize, {
                "wave": "wave", "ship": "ship", "route": "route",
                "risk": "risk", "synthesize": "synthesizer",
            })
        graph.add_edge("synthesizer", END)
        return graph.compile()

    # ─── Router ──────────────────────────────────────────────────────────────

    async def _router_node(self, state: MarineAgentState) -> MarineAgentState:
        if self._llm is None:
            state["active_agents"] = ["weather", "wave"]
            state["iteration"] = 0
            return state
        try:
            import asyncio
            prompt = f"""Maritime AI router. Query: "{state['query']}"
Respond JSON: {{"agents": ["weather","wave","ship","route","risk"], "reasoning": "..."}}
Agents: weather=storms/wind, wave=waves/ocean, ship=vessels/AIS, route=navigation, risk=danger"""
            resp = await asyncio.wait_for(self._llm.ainvoke([HumanMessage(content=prompt)]), timeout=5.0)
            data = json.loads(resp.content if isinstance(resp.content, str) else resp.content[0].get("text","[]"))
            state["active_agents"] = data.get("agents", ["weather", "wave"])
        except Exception:
            state["active_agents"] = ["weather", "wave"]
        state["iteration"] = 0
        return state

    def _decide_agents(self, state: MarineAgentState) -> str:
        agents = state.get("active_agents", [])
        return agents[0] if agents else "synthesize"

    def _next_agent_or_synthesize(self, state: MarineAgentState) -> str:
        agents = state.get("active_agents", [])
        next_idx = state.get("iteration", 0) + 1
        return agents[next_idx] if next_idx < len(agents) else "synthesize"

    # ─── Agent nodes ─────────────────────────────────────────────────────────

    async def _weather_node(self, state: MarineAgentState) -> MarineAgentState:
        result = await self.weather_agent.analyze(query=state["query"], location=state.get("location"))
        state["weather_data"] = result
        state["iteration"] = state.get("iteration", 0) + 1
        return state

    async def _wave_node(self, state: MarineAgentState) -> MarineAgentState:
        result = await self.wave_agent.analyze(
            query=state["query"], location=state.get("location"), weather_context=state.get("weather_data"))
        state["wave_data"] = result
        state["iteration"] = state.get("iteration", 0) + 1
        return state

    async def _ship_node(self, state: MarineAgentState) -> MarineAgentState:
        result = await self.ship_agent.analyze(
            query=state["query"], mmsi=state.get("vessel_mmsi"), location=state.get("location"))
        state["ship_data"] = result
        state["iteration"] = state.get("iteration", 0) + 1
        return state

    async def _route_node(self, state: MarineAgentState) -> MarineAgentState:
        result = await self.route_agent.analyze(
            query=state["query"], route_request=state.get("route_request"),
            weather=state.get("weather_data"), wave=state.get("wave_data"))
        state["route_data"] = result
        state["iteration"] = state.get("iteration", 0) + 1
        return state

    async def _risk_node(self, state: MarineAgentState) -> MarineAgentState:
        result = await self.risk_agent.analyze(
            query=state["query"], weather=state.get("weather_data"),
            wave=state.get("wave_data"), ship=state.get("ship_data"), location=state.get("location"))
        state["risk_assessment"] = result
        state["iteration"] = state.get("iteration", 0) + 1
        return state

    async def _synthesizer_node(self, state: MarineAgentState) -> MarineAgentState:
        # Always use maritime_gpt.chat for synthesis — it handles LLM + fallback
        context = {
            "weather": state.get("weather_data"),
            "waves": state.get("wave_data"),
        }
        answer = await self.maritime_gpt.chat(
            message=state["query"],
            history=[],
            context=context,
        )
        state["final_answer"] = answer
        return state

    # ─── Public ──────────────────────────────────────────────────────────────

    async def run(
        self,
        query: str,
        location: Optional[dict] = None,
        vessel_mmsi: Optional[str] = None,
        route_request: Optional[dict] = None,
    ) -> dict:
        initial: MarineAgentState = {
            "query": query, "location": location, "vessel_mmsi": vessel_mmsi,
            "route_request": route_request, "weather_data": None, "wave_data": None,
            "ship_data": None, "route_data": None, "risk_assessment": None,
            "final_answer": None, "messages": [], "active_agents": [], "iteration": 0,
        }
        result = await self.graph.ainvoke(initial)
        return {
            "answer": result.get("final_answer", "Unable to process query."),
            "weather_data": result.get("weather_data"),
            "wave_data": result.get("wave_data"),
            "ship_data": result.get("ship_data"),
            "route_data": result.get("route_data"),
            "risk_assessment": result.get("risk_assessment"),
            "agents_used": result.get("active_agents", []),
        }
