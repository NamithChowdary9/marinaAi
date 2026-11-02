"""
Maritime alert and emergency models.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from database.connection import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(50), index=True)  # storm/sos/wave/collision/weather
    severity = Column(String(20))                # info/warning/critical
    title = Column(String(300))
    description = Column(Text)

    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    region = Column(String(200), nullable=True)

    # Related entity
    mmsi = Column(String(20), nullable=True)     # vessel if applicable
    vessel_name = Column(String(200), nullable=True)

    # AI fields
    ai_recommendation = Column(Text, nullable=True)
    rescue_priority_score = Column(Float, nullable=True)

    is_active = Column(Boolean, default=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), index=True)
    raw_data = Column(JSON, nullable=True)
