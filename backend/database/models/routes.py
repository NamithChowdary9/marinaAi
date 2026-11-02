"""
Route optimization result model.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Text
from sqlalchemy.sql import func
from database.connection import Base


class RouteOptimization(Base):
    __tablename__ = "route_optimizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), index=True)

    # Input
    origin_lat = Column(Float)
    origin_lon = Column(Float)
    origin_name = Column(String(200))
    destination_lat = Column(Float)
    destination_lon = Column(Float)
    destination_name = Column(String(200))
    vessel_type = Column(String(100), nullable=True)

    # Output routes (JSON arrays of waypoints)
    safe_route = Column(JSON)
    fast_route = Column(JSON)
    fuel_route = Column(JSON)

    # Scores
    safe_route_risk_score = Column(Float)
    fast_route_risk_score = Column(Float)
    fuel_route_risk_score = Column(Float)

    estimated_distance_nm = Column(Float)   # nautical miles
    estimated_duration_h = Column(Float)    # hours
    fuel_savings_pct = Column(Float)        # % vs direct route

    ai_explanation = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
