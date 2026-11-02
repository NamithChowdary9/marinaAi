"""
Vessel / Ship database model.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from database.connection import Base


class Vessel(Base):
    __tablename__ = "vessels"

    mmsi = Column(String(20), primary_key=True, index=True)
    name = Column(String(200), nullable=True)
    vessel_type = Column(String(100), nullable=True)       # cargo, tanker, fishing, cruise
    flag = Column(String(10), nullable=True)               # country code
    callsign = Column(String(50), nullable=True)
    imo = Column(String(20), nullable=True)

    # Current position
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)                   # knots
    course = Column(Float, nullable=True)                  # degrees
    heading = Column(Float, nullable=True)
    status = Column(String(50), nullable=True)             # under way, moored, anchored...

    # Voyage info
    destination = Column(String(200), nullable=True)
    eta = Column(String(100), nullable=True)
    draught = Column(Float, nullable=True)

    # Dimensions
    length = Column(Float, nullable=True)
    width = Column(Float, nullable=True)

    # AI fields
    risk_score = Column(Float, default=0.0)                # 0-100 AI computed
    risk_level = Column(String(20), default="safe")        # safe/moderate/dangerous
    ai_alert = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())
    raw_data = Column(JSON, nullable=True)


class VesselPositionHistory(Base):
    """TimescaleDB hypertable for vessel position history."""
    __tablename__ = "vessel_position_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mmsi = Column(String(20), index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    speed = Column(Float)
    course = Column(Float)
    timestamp = Column(DateTime, server_default=func.now(), index=True)
