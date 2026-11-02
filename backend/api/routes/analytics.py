"""
Analytics API — maritime statistics and insights dashboard data.
"""

from fastapi import APIRouter
from services.ais.ais_service import AISService
from services.ocean.ocean_service import OceanService
from services.weather.weather_service import WeatherService

router = APIRouter()
ais = AISService()
ocean = OceanService()
weather = WeatherService()


@router.get("/dashboard")
async def get_dashboard_stats():
    """
    Get all data needed for the main dashboard.
    Single call to populate the entire dashboard.
    """
    ships_data = await ais.get_global_snapshot()
    global_waves = await ocean.get_global_wave_summary()

    # Count danger levels across ocean
    danger_counts = {"safe": 0, "moderate": 0, "dangerous": 0, "very_dangerous": 0}
    for region, data in global_waves.items():
        level = data.get("danger_level", "safe")
        danger_counts[level] = danger_counts.get(level, 0) + 1

    # Find max wave region
    max_wave_region = max(
        global_waves.items(),
        key=lambda x: x[1].get("wave_height_m", 0),
        default=("Unknown", {}),
    )

    return {
        "vessels": {
            "total_tracked": ships_data.get("total_vessels", 0),
            "busiest_corridors": ships_data.get("busiest_regions", []),
        },
        "ocean_conditions": {
            "safe_regions": danger_counts["safe"],
            "moderate_regions": danger_counts["moderate"],
            "dangerous_regions": danger_counts["dangerous"] + danger_counts.get("very_dangerous", 0),
            "highest_wave_region": max_wave_region[0],
            "highest_wave_height_m": max_wave_region[1].get("wave_height_m", 0),
        },
        "wave_summary": {
            region: {
                "wave_height_m": d.get("wave_height_m"),
                "danger_level": d.get("danger_level"),
                "lat": d.get("latitude"),
                "lon": d.get("longitude"),
            }
            for region, d in global_waves.items()
        },
        "ai_agents_active": 7,
        "system_status": "operational",
    }


@router.get("/ocean-regions")
async def get_ocean_region_stats():
    """Get statistics for all major ocean regions."""
    return await ocean.get_global_wave_summary()
