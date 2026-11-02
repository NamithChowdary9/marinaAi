"""
Weather API — real-time weather + wave data endpoints.
"""

from fastapi import APIRouter, Query
from services.weather.weather_service import WeatherService
from services.ocean.ocean_service import OceanService
from ml.inference.storm_predictor import StormPredictor
from ml.inference.wave_predictor import WavePredictor

router = APIRouter()
weather_service = WeatherService()
ocean_service = OceanService()
storm_predictor = StormPredictor()
wave_predictor = WavePredictor()


@router.get("/current")
async def get_current_weather(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    """Get current weather + wave data for a location."""
    weather = await weather_service.get_weather(lat, lon)
    ocean = await ocean_service.get_wave_data(lat, lon)

    # Run ML predictions
    wave_pred = wave_predictor.predict(
        wind_speed=weather.get("wind_speed_kmh", 20),
        pressure=weather.get("pressure_hpa", 1013),
        humidity=weather.get("humidity_pct", 75),
        temperature=weather.get("temperature_c", 25),
        current_wave_height=ocean.get("wave_height_m", 1.5),
    )

    storm_pred = storm_predictor.predict(
        pressure=weather.get("pressure_hpa", 1013),
        temperature=weather.get("temperature_c", 25),
        humidity=weather.get("humidity_pct", 75),
        wind_speed=weather.get("wind_speed_kmh", 20),
    )

    return {
        "location": {"lat": lat, "lon": lon},
        "weather": weather,
        "ocean": ocean,
        "ml_wave_prediction": wave_pred,
        "ml_storm_prediction": storm_pred,
        "danger_level": ocean.get("danger_level", "safe"),
    }


@router.get("/global")
async def get_global_weather():
    """Get weather overview for major maritime regions."""
    return await weather_service.get_global_maritime_weather()


@router.get("/waves/global")
async def get_global_waves():
    """Get wave conditions across all major ocean basins."""
    return await ocean_service.get_global_wave_summary()


@router.get("/waves/heatmap")
async def get_wave_heatmap():
    """
    Get wave height data formatted for heatmap rendering.
    Returns grid of {lat, lon, wave_height, danger_level} points.
    """
    # Sample key ocean points for heatmap
    points = []
    wave_data = await ocean_service.get_global_wave_summary()

    for region, data in wave_data.items():
        points.append({
            "lat": data.get("latitude"),
            "lon": data.get("longitude"),
            "wave_height_m": data.get("wave_height_m"),
            "danger_level": data.get("danger_level"),
            "region": region,
        })

    return {"heatmap_points": points, "total": len(points)}


@router.get("/storm/forecast")
async def get_storm_forecast(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Get storm probability forecast for a location."""
    weather = await weather_service.get_weather(lat, lon)
    prediction = storm_predictor.predict(
        pressure=weather.get("pressure_hpa", 1013),
        temperature=weather.get("temperature_c", 25),
        humidity=weather.get("humidity_pct", 75),
        wind_speed=weather.get("wind_speed_kmh", 20),
    )
    return {
        "location": {"lat": lat, "lon": lon},
        "current_weather": weather,
        "storm_forecast": prediction,
    }
