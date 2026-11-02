"""
Route Optimization API — AI-powered maritime route planning.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from copy import deepcopy

from agents.route.route_agent import RouteAgent
from agents.orchestrator.master_orchestrator import MasterOrchestrator

router     = APIRouter()
_route_agent = RouteAgent()
_orchestrator_instance = None  # lazy-init only for departure check


def _get_orchestrator() -> MasterOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = MasterOrchestrator()
    return _orchestrator_instance


class RouteRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    origin_name: str
    destination_lat: float
    destination_lon: float
    destination_name: str
    vessel_type: Optional[str] = "cargo"
    vessel_draft_m: Optional[float] = None
    preferred_route: Optional[str] = "safe"  # safe / fast / fuel


class VoyageTwinRequest(RouteRequest):
    """A lightweight what-if simulation built on top of the route agent."""
    scenario: str = "depart_later"  # depart_later / slow_speed / avoid_storm / engine_failure / ais_loss
    departure_offset_h: float = 6
    speed_knots: float = 12


@router.post("/optimize")
async def optimize_route(request: RouteRequest):
    """
    AI-powered maritime route optimization.
    Calls RouteAgent directly — bypasses orchestrator to guarantee route data is returned.
    """
    query = (
        f"Optimize route from {request.origin_name} ({request.origin_lat}, {request.origin_lon}) "
        f"to {request.destination_name} ({request.destination_lat}, {request.destination_lon}) "
        f"for a {request.vessel_type} vessel. Preferred route type: {request.preferred_route}."
    )

    # ── Call RouteAgent directly (reliable, always returns data) ──────────────
    route_data = await _route_agent.analyze(
        query=query,
        route_request={
            "origin":      {"lat": request.origin_lat,      "lon": request.origin_lon,      "name": request.origin_name},
            "destination": {"lat": request.destination_lat, "lon": request.destination_lon, "name": request.destination_name},
            "vessel_type": request.vessel_type,
            "preferred":   request.preferred_route,
        },
        weather=None,
        wave=None,
    )

    # Normalise — route_data might be wrapped or bare
    if "routes" not in route_data:
        route_data = {}
    routes = route_data.get("routes", {})
    recommended = route_data.get("recommended_route", request.preferred_route or "safe")

    # Build structured AI recommendation with directions
    def _format_route_block(label: str, icon: str, route: dict) -> str:
        if not route:
            return ""
        wps = route.get("waypoints", [])
        dirs = route.get("directions", [])
        lines = [f"{icon} **{label}**"]
        lines.append(f"  📏 {route.get('distance_nm', '—')} nm  |  ⏱ {route.get('duration_h', '—'):.0f}h  |  ⚠️ Risk {route.get('risk_score', '—')}/100")
        if route.get("fuel_savings_pct"):
            lines.append(f"  ⛽ Fuel saving: {route['fuel_savings_pct']}%")
        if wps:
            lines.append("  📍 Waypoints: " + " → ".join(w["name"] for w in wps[:6]))
        if dirs:
            lines.append("  🧭 Directions:")
            for i, d in enumerate(dirs[:6], 1):
                lines.append(f"     {i}. {d}")
        if route.get("description"):
            lines.append(f"  ℹ️  {route['description']}")
        return "\n".join(lines)

    hazards = route_data.get("hazards_on_path", [])
    departure_advice = route_data.get("departure_advice", "")
    reasoning = route_data.get("reasoning", "")

    ai_rec_parts = [
        f"🗺️ **Route: {request.origin_name} → {request.destination_name}**",
        f"🚢 Vessel: {request.vessel_type or 'cargo'}  |  ✅ Recommended: **{recommended.replace('_', ' ').title()}**",
        (f"💡 {reasoning}" if reasoning else ""),
        "",
    ]

    for key, label, icon in [("safe", "Safe Route", "🛡"), ("fast", "Fast Route", "⚡"), ("fuel_efficient", "Eco Route", "⛽")]:
        block = _format_route_block(label, icon, routes.get(key, {}))
        if block:
            ai_rec_parts.append(block)
            ai_rec_parts.append("")

    if hazards:
        ai_rec_parts.append("⚠️ **Hazards Along Route:**")
        for h in hazards:
            ai_rec_parts.append(f"  • {h}")
        ai_rec_parts.append("")

    if departure_advice:
        ai_rec_parts.append(f"🕐 **Departure Advice:** {departure_advice}")

    structured_ai_recommendation = "\n".join(p for p in ai_rec_parts if p is not None)

    return {
        "query": query,
        "route_options": route_data,
        "weather_along_route": None,
        "risk_assessment":     None,
        "ai_recommendation":   structured_ai_recommendation,
        "agents_used":         ["route"],
    }


@router.post("/voyage-twin")
async def voyage_twin(request: VoyageTwinRequest):
    """Compare the current voyage plan with a selected operational what-if.

    This deliberately uses the route agent's deterministic lane data as its base so
    a useful demo is available even when live weather providers are unavailable.
    Live weather can later be folded into the risk modifiers here without changing
    the client contract.
    """
    route_data = await _route_agent.analyze(
        query=(f"Build voyage twin from {request.origin_name} to {request.destination_name}. "
               f"Vessel: {request.vessel_type}. Scenario: {request.scenario}."),
        route_request={
            "origin": {"lat": request.origin_lat, "lon": request.origin_lon, "name": request.origin_name},
            "destination": {"lat": request.destination_lat, "lon": request.destination_lon, "name": request.destination_name},
            "vessel_type": request.vessel_type,
            "preferred": request.preferred_route,
        },
        weather=None,
        wave=None,
    )
    routes: Dict[str, Any] = route_data.get("routes", {})
    baseline_key = request.preferred_route if request.preferred_route in routes else route_data.get("recommended_route", "safe")
    baseline = deepcopy(routes.get(baseline_key) or routes.get("safe") or next(iter(routes.values()), {}))
    safe_route = deepcopy(routes.get("safe") or baseline)
    eco_route = deepcopy(routes.get("fuel_efficient") or baseline)

    def plan(identifier: str, label: str, route: dict, risk_delta: float, duration_factor: float,
             fuel_factor: float, summary: str, why: str) -> dict:
        data = deepcopy(route)
        data["risk_score"] = max(0, min(100, round(float(data.get("risk_score", 35)) + risk_delta)))
        data["duration_h"] = round(float(data.get("duration_h", 0)) * duration_factor, 1)
        # Relative fuel index keeps the comparison meaningful across vessel sizes.
        data["fuel_index"] = round(max(1, 100 * fuel_factor))
        return {"id": identifier, "label": label, "route": data, "summary": summary, "why": why}

    current = plan(
        "current", "Current plan", baseline, 0, 1, 1,
        "Sails on the current schedule and standard operating profile.",
        "This is the reference plan used to measure the operational trade-off.",
    )

    scenario = request.scenario
    if scenario == "slow_speed":
        speed = max(8, min(22, request.speed_knots))
        assumed_base_speed = 16
        simulated = plan(
            "simulated", f"Cruise at {speed:g} knots", eco_route, -8, assumed_base_speed / speed, (speed / assumed_base_speed) ** 2,
            "Lower engine load cuts fuel use and gives more room to manage traffic.",
            f"Reducing speed to {speed:g} knots increases ETA but materially lowers the fuel index.",
        )
    elif scenario == "avoid_storm":
        simulated = plan(
            "simulated", "Weather-avoidance route", safe_route, -22, 1.12, 1.08,
            "Uses the safer lane as a weather-avoidance corridor.",
            "The detour adds distance, but avoids the higher-exposure portion of the direct passage.",
        )
    elif scenario == "engine_failure":
        simulated = plan(
            "simulated", "Engine contingency", safe_route, 38, 1.45, 1.18,
            "Assumes reduced propulsion and a conservative corridor near support options.",
            "Loss of propulsion greatly raises exposure; arrange assistance and reassess before sailing.",
        )
    elif scenario == "ais_loss":
        simulated = plan(
            "simulated", "AIS-loss protocol", safe_route, 28, 1.10, 1.04,
            "Assumes restricted-speed operation with manual reporting and extra watchkeeping.",
            "Without AIS visibility, collision-management margins shrink and traffic separation is preferred.",
        )
    else:
        hours = max(1, min(48, request.departure_offset_h))
        simulated = plan(
            "simulated", f"Depart +{hours:g} hours", safe_route, -18, 1.04, 1.03,
            "Waits for the next safer departure window before using the lower-risk lane.",
            f"A {hours:g}-hour delay shifts the voyage into a calmer operational window in this simulation.",
        )

    # A third choice is always present: the route agent's low-fuel plan.
    eco = plan(
        "eco", "Eco alternative", eco_route, -5, 1.10, 0.82,
        "A steady eco-speed option for lower fuel burn and a moderate schedule trade-off.",
        "Maintaining a lower, stable speed reduces fuel use while preserving a conservative risk profile.",
    )
    plans = [current, simulated, eco]
    recommendation = min(plans, key=lambda p: (p["route"]["risk_score"] * 1.8 + p["route"]["duration_h"] * 0.08 + p["route"]["fuel_index"] * 0.12))
    high_risk = recommendation["route"]["risk_score"] >= 60
    recommendation_text = (
        f"{recommendation['label']} is the best balance for this voyage. {recommendation['why']}"
        if not high_risk else
        f"{recommendation['label']} is the least-exposed option, but the simulated risk remains high. "
        "Treat this as a planning prompt and obtain operational approval before departure."
    )

    return {
        "voyage": {"origin": request.origin_name, "destination": request.destination_name, "vessel_type": request.vessel_type},
        "scenario": scenario,
        "plans": plans,
        "recommended_plan_id": recommendation["id"],
        "recommendation": recommendation_text,
        "hazards": route_data.get("hazards_on_path", []),
        "data_note": "Planning simulation based on MarineAI route-lane intelligence; validate against current official notices and onboard systems.",
    }


@router.get("/departure-check")
async def departure_safety_check(
    port: str,
    lat: float,
    lon: float,
    vessel_type: str = "fishing",
    departure_time: Optional[str] = None,
):
    """Check if it's safe to depart from a port."""
    query = (
        f"Is it safe to depart from {port} ({lat}, {lon}) "
        f"with a {vessel_type} vessel"
        f"{' at ' + departure_time if departure_time else ''}? "
        f"Check wave height, wind speed, visibility, and storm probability."
    )

    orch   = _get_orchestrator()
    result = await orch.run(query=query, location={"lat": lat, "lon": lon, "name": port})

    weather = result.get("weather_data", {})
    wave = result.get("wave_data", {})
    risk = result.get("risk_assessment", {})

    # Determine safe/unsafe
    wave_h = wave.get("current_waves", {}).get("height_m") if wave else None
    risk_score = risk.get("overall_risk_score", 0) if risk else 0

    is_safe = risk_score < 50 and (wave_h is None or wave_h < 4.0)

    return {
        "port": port,
        "vessel_type": vessel_type,
        "departure_time": departure_time,
        "is_safe_to_depart": is_safe,
        "safety_verdict": "✅ Safe to depart" if is_safe else "⚠️ Departure not recommended",
        "risk_score": risk_score,
        "ai_explanation": result.get("answer"),
        "weather": weather,
        "wave": wave,
        "agents_used": result.get("agents_used", []),
    }
