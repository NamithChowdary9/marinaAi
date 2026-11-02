"""
Weather and ocean condition data models.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, JSON
from sqlalchemy.sql import func
from database.connection import Base


class WeatherSnapshot(Base):
    __tablename__ = "weather_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(String(200), index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    grid_lat = Column(Float)   # snapped to 0.5° grid
    grid_lon = Column(Float)

    # Weather
    temperature = Column(Float)         # °C
    wind_speed = Column(Float)          # km/h
    wind_direction = Column(Float)      # degrees
    pressure = Column(Float)            # hPa
    humidity = Column(Float)            # %
    precipitation = Column(Float)       # mm
    visibility = Column(Float)          # km
    weather_condition = Column(String(100))

    # Ocean / Waves
    wave_height = Column(Float)         # meters
    wave_period = Column(Float)         # seconds
    wave_direction = Column(Float)      # degrees
    current_speed = Column(Float)       # knots
    current_direction = Column(Float)

    # AI predictions
    predicted_wave_height_6h = Column(Float)
    predicted_wave_height_24h = Column(Float)
    predicted_wave_height_72h = Column(Float)
    storm_probability = Column(Float)   # 0-1
    danger_level = Column(String(20))   # safe/moderate/dangerous

    timestamp = Column(DateTime, server_default=func.now(), index=True)
    raw_data = Column(JSON, nullable=True)
