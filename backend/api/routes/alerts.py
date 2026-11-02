"""
Alerts API — maritime emergency and danger zone alerts.
"""

from fastapi import APIRouter, Query
from typing import Optional, List

from services.weather.weather_service import WeatherService
from services.ocean.ocean_service import OceanService
from ml.inference.storm_predictor import StormPredictor

router = APIRouter()
weather_service = WeatherService()
ocean_service = OceanService()
storm_predictor = StormPredictor()


@router.get("/active")
async def get_active_alerts():
    """Get all currently active maritime alerts."""
    # Get weather across regions and generate alerts
    global_weather = await weather_service.get_global_maritime_weather()
    global_waves = await ocean_service.get_global_wave_summary()

    alerts = []

    for region, weather in global_weather.items():
        wind = weather.get("wind_speed_kmh", 0)
        pressure = weather.get("pressure_hpa", 1013)
        humidity = weather.get("humidity_pct", 70)
        temp = weather.get("temperature_c", 25)

        # Check storm probability
        storm = storm_predictor.predict(
            pressure=pressure,
            temperature=temp,
            humidity=humidity,
            wind_speed=wind,
        )

        if storm.get("should_alert"):
            alerts.append({
                "type": "storm",
                "severity": storm.get("severity", "medium"),
                "title": f"Storm Alert — {region}",
                "description": (
                    f"Storm probability {storm['storm_probability_6h']*100:.0f}% in next 6h. "
                    f"Category: {storm['category']}. Wind: {wind:.0f} km/h."
                ),
                "region": region,
                "storm_data": storm,
            })

    for region, waves in global_waves.items():
        wave_h = waves.get("wave_height_m", 0)
        if wave_h >= 4.0:
            severity = "critical" if wave_h >= 6 else "warning"
            alerts.append({
                "type": "wave",
                "severity": severity,
                "title": f"High Waves — {region}",
                "description": (
                    f"Wave height {wave_h:.1f}m in {region}. "
                    f"{'DANGEROUS for all vessels.' if wave_h >= 6 else 'Caution advised for small vessels.'}"
                ),
                "region": region,
                "wave_height_m": wave_h,
                "latitude": waves.get("latitude"),
                "longitude": waves.get("longitude"),
            })

    # Sort by severity
    severity_order = {"critical": 0, "extreme": 0, "warning": 1, "medium": 2, "low": 3}
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 4))

    return {"total": len(alerts), "alerts": alerts}


@router.get("/danger-zones")
async def get_danger_zones():
    """Get all current danger zones on the ocean."""
    global_waves = await ocean_service.get_global_wave_summary()
    global_weather = await weather_service.get_global_maritime_weather()

    zones = []
    for region, wave_data in global_waves.items():
        level = wave_data.get("danger_level", "safe")
        if level in ("dangerous", "very_dangerous", "moderate"):
            zones.append({
                "region": region,
                "latitude": wave_data.get("latitude"),
                "longitude": wave_data.get("longitude"),
                "danger_level": level,
                "primary_threat": "high_waves",
                "wave_height_m": wave_data.get("wave_height_m"),
                "color": "red" if "dangerous" in level else "yellow",
            })

    for region, weather in global_weather.items():
        if weather.get("wind_speed_kmh", 0) > 50:
            zones.append({
                "region": region,
                "danger_level": "dangerous",
                "primary_threat": "high_winds",
                "wind_speed_kmh": weather.get("wind_speed_kmh"),
                "color": "red",
            })

    return {"total": len(zones), "danger_zones": zones}
