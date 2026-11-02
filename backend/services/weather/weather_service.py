"""
Weather Service — fetches data from OpenWeatherMap and Open-Meteo.
"""

import httpx
from loguru import logger
from typing import Optional

from config.settings import settings


class WeatherService:
    OWM_BASE = "https://api.openweathermap.org/data/2.5"
    OPEN_METEO_MARINE = "https://marine-api.open-meteo.com/v1/marine"

    async def get_weather(self, lat: float, lon: float) -> dict:
        """Get current weather for a coordinate."""
        owm_data = await self._get_owm_weather(lat, lon)
        marine_data = await self._get_open_meteo_marine(lat, lon)
        # owm_data takes priority — merge marine on top but don't overwrite real OWM fields
        merged = {**marine_data, **owm_data, "latitude": lat, "longitude": lon}
        return merged

    async def get_global_maritime_weather(self) -> dict:
        """Get weather for major maritime regions — concurrent calls."""
        import asyncio
        regions = {
            "Indian Ocean": (5.0, 75.0),
            "Arabian Sea": (15.0, 65.0),
            "Bay of Bengal": (12.0, 87.0),
            "South China Sea": (12.0, 113.0),
            "North Atlantic": (45.0, -30.0),
            "Pacific": (10.0, 160.0),
        }
        async def fetch(name, lat, lon):
            try:
                return name, await asyncio.wait_for(self.get_weather(lat, lon), timeout=8.0)
            except Exception as e:
                logger.warning(f"Weather fetch failed for {name}: {e}")
                return name, self._mock_weather(lat, lon)
        results = await asyncio.gather(*[fetch(n, lat, lon) for n, (lat, lon) in regions.items()])
        return dict(results)

    async def _get_owm_weather(self, lat: float, lon: float) -> dict:
        """OpenWeatherMap current weather."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.OWM_BASE}/weather",
                    params={
                        "lat": lat, "lon": lon,
                        "appid": settings.openweather_api_key,
                        "units": "metric",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "temperature_c": data["main"]["temp"],
                        "feels_like_c": data["main"]["feels_like"],
                        "humidity_pct": data["main"]["humidity"],
                        "pressure_hpa": data["main"]["pressure"],
                        "wind_speed_kmh": data["wind"]["speed"] * 3.6,
                        "wind_direction_deg": data["wind"].get("deg", 0),
                        "visibility_km": data.get("visibility", 10000) / 1000,
                        "weather_condition": data["weather"][0]["main"],
                        "weather_description": data["weather"][0]["description"],
                        "precipitation_mm": data.get("rain", {}).get("1h", 0),
                    }
        except Exception as e:
            logger.warning(f"OWM API error: {e}")
        return self._mock_weather(lat, lon)

    async def _get_open_meteo_marine(self, lat: float, lon: float) -> dict:
        """Open-Meteo Marine API for wave data (free, no key needed)."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    self.OPEN_METEO_MARINE,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current": "wave_height,wave_direction,wave_period,wind_wave_height,swell_wave_height",
                        "hourly": "wave_height,wave_direction,wave_period,wind_wave_height,swell_wave_height",
                        "forecast_days": 4,
                        "timezone": "auto",
                        "cell_selection": "sea",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    current = data.get("current", {})
                    hourly = data.get("hourly", {})
                    wave_heights = hourly.get("wave_height", [1.0])
                    wave_dirs = hourly.get("wave_direction", [180])
                    wave_periods = hourly.get("wave_period", [8])
                    return {
                        "wave_height_m": current.get("wave_height") or (wave_heights[0] if wave_heights else 1.0),
                        "wave_direction_deg": current.get("wave_direction") or (wave_dirs[0] if wave_dirs else 180),
                        "wave_period_s": current.get("wave_period") or (wave_periods[0] if wave_periods else 8),
                        "wave_forecast_6h": wave_heights[6] if len(wave_heights) > 6 else 1.0,
                        "wave_forecast_24h": wave_heights[24] if len(wave_heights) > 24 else 1.0,
                        "wave_forecast_72h": wave_heights[72] if len(wave_heights) > 72 else 1.0,
                    }
        except Exception as e:
            logger.warning(f"Open-Meteo marine error: {e}")
        return {
            "wave_height_m": 1.5,
            "wave_direction_deg": 180,
            "wave_period_s": 8,
            "wave_forecast_6h": 1.5,
            "wave_forecast_24h": 2.0,
            "wave_forecast_72h": 1.8,
        }

    def _mock_weather(self, lat: float, lon: float) -> dict:
        """Fallback mock data when APIs are unavailable."""
        import random
        return {
            "temperature_c": round(random.uniform(20, 32), 1),
            "humidity_pct": round(random.uniform(60, 90), 0),
            "pressure_hpa": round(random.uniform(1005, 1020), 0),
            "wind_speed_kmh": round(random.uniform(10, 45), 1),
            "wind_direction_deg": round(random.uniform(0, 360), 0),
            "visibility_km": round(random.uniform(5, 20), 1),
            "weather_condition": random.choice(["Clear", "Cloudy", "Rain", "Thunderstorm"]),
            "weather_description": "mock data — configure OPENWEATHER_API_KEY",
            "precipitation_mm": round(random.uniform(0, 10), 1),
            "wave_height_m": round(random.uniform(0.5, 4.0), 1),
            "wave_direction_deg": 180,
            "wave_period_s": 8,
        }
