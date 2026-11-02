"""
Vessel Collision Risk Prediction.
Analyzes AIS data to predict collision probability between vessels.
"""

import numpy as np
import math
from typing import List, Dict


class CollisionPredictor:
    """
    Predicts collision probability between two vessels using
    CPA (Closest Point of Approach) analysis + ML risk scoring.
    """

    # Safe passing distances
    SAFE_CPA_NM = 0.5       # 0.5 nautical miles
    CRITICAL_CPA_NM = 0.1   # 0.1 nm = critical

    def predict_pair(self, vessel_a: dict, vessel_b: dict) -> dict:
        """
        Calculate collision risk between two vessels.
        
        Args:
            vessel_a, vessel_b: dicts with lat, lon, speed, course
        """
        cpa, tcpa = self._compute_cpa(vessel_a, vessel_b)
        risk_score = self._compute_risk(cpa, tcpa, vessel_a, vessel_b)
        risk_level = self._classify_risk(risk_score)

        return {
            "vessel_a_mmsi": vessel_a.get("mmsi"),
            "vessel_b_mmsi": vessel_b.get("mmsi"),
            "cpa_nm": round(cpa, 3),
            "tcpa_minutes": round(tcpa, 1),
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "recommendation": self._get_recommendation(risk_level, cpa, tcpa),
        }

    def analyze_fleet(self, vessels: List[dict]) -> List[dict]:
        """Analyze collision risk for all vessel pairs."""
        risks = []
        for i in range(len(vessels)):
            for j in range(i + 1, len(vessels)):
                result = self.predict_pair(vessels[i], vessels[j])
                if result["risk_score"] > 0.2:
                    risks.append(result)
        return sorted(risks, key=lambda x: x["risk_score"], reverse=True)[:20]

    def _compute_cpa(self, a: dict, b: dict) -> tuple:
        """
        Compute CPA (Closest Point of Approach) and TCPA.
        Using simplified 2D vector math.
        """
        # Convert to approximate Cartesian (good for short distances)
        lat_scale = 111.12  # km per degree lat
        lon_scale = 111.12 * math.cos(math.radians((a["latitude"] + b["latitude"]) / 2))

        ax = a["longitude"] * lon_scale
        ay = a["latitude"] * lat_scale
        bx = b["longitude"] * lon_scale
        by = b["latitude"] * lat_scale

        # Velocities
        a_course_rad = math.radians(a.get("course", 0))
        b_course_rad = math.radians(b.get("course", 0))
        a_speed = a.get("speed", 0) * 1.852  # knots → km/h
        b_speed = b.get("speed", 0) * 1.852

        vax = a_speed * math.sin(a_course_rad)
        vay = a_speed * math.cos(a_course_rad)
        vbx = b_speed * math.sin(b_course_rad)
        vby = b_speed * math.cos(b_course_rad)

        # Relative position and velocity
        dx = bx - ax
        dy = by - ay
        dvx = vbx - vax
        dvy = vby - vay

        # Time of CPA
        dv_sq = dvx**2 + dvy**2
        if dv_sq < 0.0001:
            tcpa_h = 0
        else:
            tcpa_h = -(dx * dvx + dy * dvy) / dv_sq

        tcpa_h = max(0, tcpa_h)

        # CPA distance
        cpa_x = dx + dvx * tcpa_h
        cpa_y = dy + dvy * tcpa_h
        cpa_km = math.sqrt(cpa_x**2 + cpa_y**2)
        cpa_nm = cpa_km / 1.852

        return cpa_nm, tcpa_h * 60  # return in NM and minutes

    def _compute_risk(self, cpa_nm: float, tcpa_min: float, a: dict, b: dict) -> float:
        """Compute 0-1 risk score."""
        if cpa_nm > 2.0 or tcpa_min < 0:
            return 0.0

        # CPA risk component
        cpa_risk = max(0, 1 - cpa_nm / 2.0)

        # TCPA risk component (risk higher if close encounter in next 30 min)
        tcpa_risk = max(0, 1 - tcpa_min / 30)

        # Speed risk
        combined_speed = a.get("speed", 0) + b.get("speed", 0)
        speed_risk = min(1.0, combined_speed / 40)

        return round(0.5 * cpa_risk + 0.3 * tcpa_risk + 0.2 * speed_risk, 3)

    def _classify_risk(self, score: float) -> str:
        if score >= 0.75:
            return "critical"
        elif score >= 0.5:
            return "high"
        elif score >= 0.25:
            return "medium"
        else:
            return "low"

    def _get_recommendation(self, risk_level: str, cpa: float, tcpa: float) -> str:
        if risk_level == "critical":
            return f"IMMEDIATE ACTION REQUIRED. CPA {cpa:.1f}nm in {tcpa:.0f} min. Alter course now."
        elif risk_level == "high":
            return f"High collision risk. CPA {cpa:.1f}nm in {tcpa:.0f} min. Monitor closely and prepare to maneuver."
        elif risk_level == "medium":
            return f"Moderate risk. CPA {cpa:.1f}nm. Maintain watch."
        else:
            return "Situation normal."
