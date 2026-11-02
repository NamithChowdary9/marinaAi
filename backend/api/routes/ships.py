"""
Ships API — vessel tracking endpoints + WebSocket live feed.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from typing import Optional
import asyncio
import json

from services.ais.ais_service import AISService
from ml.inference.collision_predictor import CollisionPredictor

router = APIRouter()
ais_service = AISService()
collision_predictor = CollisionPredictor()

# Connected WebSocket clients
_ws_clients: set = set()


@router.get("/")
async def get_all_vessels(
    lat_min: Optional[float] = None,
    lat_max: Optional[float] = None,
    lon_min: Optional[float] = None,
    lon_max: Optional[float] = None,
    vessel_type: Optional[str] = None,
    limit: int = Query(default=500, ge=1, le=2000),
):
    """Get all tracked vessels, optionally filtered by bounding box."""
    data = await ais_service.get_global_snapshot()
    vessels = data.get("vessels", [])

    # Apply bounding box filter
    bounds = (lat_min, lat_max, lon_min, lon_max)
    if any(value is not None for value in bounds) and any(value is None for value in bounds):
        raise HTTPException(status_code=422, detail="Provide all bounding-box coordinates together")
    if all(value is not None for value in bounds):
        if lat_min > lat_max or lon_min > lon_max:
            raise HTTPException(status_code=422, detail="Minimum bounds must not exceed maximum bounds")
        vessels = [
            v for v in vessels
            if lat_min <= v.get("latitude", 0) <= lat_max
            and lon_min <= v.get("longitude", 0) <= lon_max
        ]

    # Apply vessel type filter
    if vessel_type:
        vessels = [v for v in vessels if v.get("vessel_type", "").lower() == vessel_type.lower()]

    return {
        "total": len(vessels),
        "vessels": vessels[:limit],
        "stats": data.get("busiest_regions", []),
    }


@router.get("/area/search")
async def get_vessels_in_area(
    lat: float = Query(..., ge=-90, le=90, description="Center latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Center longitude"),
    radius: float = Query(default=100.0, gt=0, le=500, description="Search radius in nautical miles"),
):
    """Get all vessels within a radius of a coordinate."""
    vessels = await ais_service.get_vessels_in_area(lat=lat, lon=lon, radius_nm=radius)
    return {"total": len(vessels), "vessels": vessels, "center": {"lat": lat, "lon": lon}, "radius_nm": radius}


@router.get("/collision/risks")
async def get_collision_risks(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius: float = Query(default=50.0, gt=0, le=500),
):
    """Get collision risk analysis for vessels in an area."""
    vessels = await ais_service.get_vessels_in_area(lat=lat, lon=lon, radius_nm=radius)
    risks = collision_predictor.analyze_fleet(vessels)
    return {
        "total_vessels": len(vessels),
        "collision_risks": risks,
        "high_risk_count": len([r for r in risks if r["risk_level"] in ("high", "critical")]),
    }


@router.get("/{mmsi}")
async def get_vessel(mmsi: str):
    """Get detailed info for a specific vessel."""
    vessel = await ais_service.get_vessel(mmsi)
    if not vessel:
        raise HTTPException(status_code=404, detail=f"Vessel {mmsi} not found")
    return vessel


@router.get("/{mmsi}/risk")
async def get_vessel_risk(mmsi: str):
    """Get AI risk assessment for a specific vessel."""
    from agents.orchestrator.master_orchestrator import MasterOrchestrator
    vessel = await ais_service.get_vessel(mmsi)
    if not vessel:
        raise HTTPException(status_code=404, detail=f"Vessel {mmsi} not found")

    orchestrator = MasterOrchestrator()
    result = await orchestrator.run(
        query=f"What is the risk level for vessel {vessel.get('name', mmsi)} at position {vessel.get('latitude')}, {vessel.get('longitude')}?",
        location={"lat": vessel.get("latitude"), "lon": vessel.get("longitude")},
        vessel_mmsi=mmsi,
    )
    return {
        "mmsi": mmsi,
        "vessel_name": vessel.get("name"),
        "risk_assessment": result.get("risk_assessment"),
        "weather_at_location": result.get("weather_data"),
        "wave_at_location": result.get("wave_data"),
        "ai_summary": result.get("answer"),
    }


@router.websocket("/ws/live")
async def vessel_live_stream(websocket: WebSocket):
    """WebSocket endpoint for live vessel position updates."""
    await websocket.accept()
    _ws_clients.add(websocket)
    send_lock = asyncio.Lock()

    async def send_update(message: dict):
        """Serialize sends because stream callbacks and heartbeats run concurrently."""
        async with send_lock:
            await websocket.send_json(message)

    stream_service = getattr(websocket.app.state, "ais_service", None)
    if stream_service:
        stream_service.subscribe(send_update)

    try:
        # Send initial snapshot
        data = await ais_service.get_global_snapshot()
        await send_update({"type": "snapshot", "vessels": data["vessels"]})

        # Keep connection alive + send heartbeat
        while True:
            await asyncio.sleep(30)
            await send_update({"type": "heartbeat", "status": "ok"})

    except WebSocketDisconnect:
        pass
    finally:
        _ws_clients.discard(websocket)
        if stream_service:
            stream_service.unsubscribe(send_update)
