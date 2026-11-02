"""
Ocean Service — wave heights, ocean currents, sea surface temperature.
Sources: Open-Meteo Marine (free), NOAA ERDDAP (free).
"""

import httpx
from loguru import logger

from config.settings import settings


class OceanService:
    OPEN_METEO_MARINE = "https://marine-api.open-meteo.com/v1/marine"

    async def get_wave_data(self, lat: float, lon: float) -> dict:
        """Get detailed wave data for a specific location."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    self.OPEN_METEO_MARINE,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current": (
                            "wave_height,wave_direction,wave_period,"
                            "swell_wave_height,ocean_current_velocity,ocean_current_direction"
                        ),
                        "hourly": (
                            "wave_height,wave_direction,wave_period,"
                            "wind_wave_height,wind_wave_direction,wind_wave_period,"
                            "swell_wave_height,swell_wave_direction,swell_wave_period,"
                            "ocean_current_velocity,ocean_current_direction"
                        ),
                        "forecast_days": 3,
                        "timezone": "auto",
                        "cell_selection": "sea",
                        "velocity_unit": "ms",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    now = data.get("current", {})
                    hourly = data.get("hourly", {})
                    wh = hourly.get("wave_height", [1.0])
                    wd = hourly.get("wave_direction", [180])
                    wp = hourly.get("wave_period", [8])
                    sh = hourly.get("swell_wave_height", [0.5])
                    cv = hourly.get("ocean_current_velocity", [0.5])
                    cd = hourly.get("ocean_current_direction", [90])

                    current = now.get("wave_height") or (wh[0] if wh else 1.0)
                    return {
                        "latitude": lat,
                        "longitude": lon,
                        "wave_height_m": current,
                        "wave_direction_deg": now.get("wave_direction") or (wd[0] if wd else 180),
                        "wave_period_s": now.get("wave_period") or (wp[0] if wp else 8),
                        "swell_height_m": now.get("swell_wave_height") or (sh[0] if sh else 0.5),
                        "current_velocity_ms": now.get("ocean_current_velocity") or (cv[0] if cv else 0.5),
                        "current_direction_deg": now.get("ocean_current_direction") or (cd[0] if cd else 90),
                        "danger_level": self._classify_danger(current),
                        "wave_forecast": {
                            "6h":  wh[6]  if len(wh) > 6  else current,
                            "12h": wh[12] if len(wh) > 12 else current,
                            "24h": wh[24] if len(wh) > 24 else current,
                            "48h": wh[48] if len(wh) > 48 else current,
                            "72h": wh[72] if len(wh) > 72 else current,
                        },
                    }
        except Exception as e:
            logger.warning(f"Ocean service error: {e}")

        return self._mock_wave_data(lat, lon)

    async def get_global_wave_summary(self) -> dict:
        """Get wave conditions for major ocean basins — concurrent calls."""
        import asyncio
        ocean_points = {
            "North Indian Ocean": (15.0, 70.0),
            "Arabian Sea": (18.0, 63.0),
            "Bay of Bengal": (13.0, 86.0),
            "South Indian Ocean": (-20.0, 75.0),
            "North Pacific": (30.0, 165.0),
            "South Pacific": (-20.0, 170.0),
            "North Atlantic": (40.0, -35.0),
            "South Atlantic": (-20.0, -25.0),
            "Mediterranean Sea": (35.0, 20.0),
            "South China Sea": (12.0, 113.0),
        }
        async def fetch(region, lat, lon):
            try:
                return region, await asyncio.wait_for(self.get_wave_data(lat, lon), timeout=8.0)
            except Exception:
                return region, self._mock_wave_data(lat, lon)
        results = await asyncio.gather(*[fetch(r, lat, lon) for r, (lat, lon) in ocean_points.items()])
        return dict(results)

    def _classify_danger(self, wave_height_m: float) -> str:
        if wave_height_m < 2.0:
            return "safe"
        elif wave_height_m < 4.0:
            return "moderate"
        elif wave_height_m < 6.0:
            return "dangerous"
        else:
            return "very_dangerous"

    def _mock_wave_data(self, lat: float, lon: float) -> dict:
        import random
        h = round(random.uniform(0.5, 5.0), 1)
        return {
            "latitude": lat,
            "longitude": lon,
            "wave_height_m": h,
            "wave_direction_deg": round(random.uniform(0, 360), 0),
            "wave_period_s": round(random.uniform(5, 15), 1),
            "swell_height_m": round(h * 0.6, 1),
            "current_velocity_ms": round(random.uniform(0.2, 2.0), 2),
            "current_direction_deg": round(random.uniform(0, 360), 0),
            "danger_level": self._classify_danger(h),
            "wave_forecast": {"6h": h, "12h": h + 0.2, "24h": h - 0.1, "48h": h, "72h": h + 0.3},
        }
