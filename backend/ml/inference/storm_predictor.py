"""
Storm Prediction Model — predicts storm probability using an LSTM/Transformer.
"""

import numpy as np
import os
import joblib
from loguru import logger
from typing import Optional

from config.settings import settings


class StormPredictor:
    """
    Predicts storm formation probability from weather inputs.
    
    Inputs: pressure, temperature, humidity, wind_speed, wind_change_rate
    Output: storm probability (0.0 – 1.0) for 6h, 24h, 72h windows
    """

    CATEGORY_THRESHOLDS = {
        "tropical_depression": 0.3,
        "tropical_storm": 0.5,
        "cyclone_cat1": 0.65,
        "cyclone_cat2": 0.75,
        "cyclone_cat3": 0.85,
    }

    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        model_path = os.path.join(settings.ml_models_dir, "storm_prediction_model.pkl")
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                logger.info("Storm prediction model loaded")
            except Exception as e:
                logger.warning(f"Could not load storm model: {e}")

    def predict(
        self,
        pressure: float,
        temperature: float,
        humidity: float,
        wind_speed: float,
        sea_surface_temp: Optional[float] = None,
    ) -> dict:
        """Predict storm probability."""
        sst = sea_surface_temp or temperature

        if self.model is not None:
            try:
                features = np.array([[pressure, temperature, humidity, wind_speed, sst]])
                probs = self.model.predict_proba(features)[0]
                prob_6h = float(probs[1])
                return self._format_result(prob_6h, wind_speed, pressure)
            except Exception as e:
                logger.warning(f"Storm model inference failed: {e}")

        return self._heuristic_estimate(pressure, wind_speed, humidity, sst)

    def _heuristic_estimate(
        self, pressure: float, wind_speed: float, humidity: float, sst: float
    ) -> dict:
        """Rule-based storm probability estimation."""
        prob = 0.0

        # Low pressure is the primary storm driver
        if pressure < 980:
            prob += 0.6
        elif pressure < 995:
            prob += 0.3
        elif pressure < 1005:
            prob += 0.1

        # High wind speed
        if wind_speed > 60:
            prob += 0.3
        elif wind_speed > 40:
            prob += 0.15
        elif wind_speed > 25:
            prob += 0.05

        # High humidity and warm sea
        if humidity > 85 and sst > 27:
            prob += 0.15

        prob = min(prob, 0.99)
        return self._format_result(prob, wind_speed, pressure)

    def _format_result(self, prob_6h: float, wind_speed: float, pressure: float) -> dict:
        """Format storm prediction result."""
        # Probability decreases over longer horizons (uncertainty)
        prob_24h = prob_6h * 0.8
        prob_72h = prob_6h * 0.6

        category = "none"
        for cat, threshold in self.CATEGORY_THRESHOLDS.items():
            if prob_6h >= threshold:
                category = cat

        severity = "none"
        if prob_6h >= 0.85:
            severity = "extreme"
        elif prob_6h >= 0.65:
            severity = "high"
        elif prob_6h >= 0.40:
            severity = "medium"
        elif prob_6h >= 0.20:
            severity = "low"

        return {
            "storm_probability_6h":  round(prob_6h, 3),
            "storm_probability_24h": round(prob_24h, 3),
            "storm_probability_72h": round(prob_72h, 3),
            "category": category,
            "severity": severity,
            "wind_speed_kmh": wind_speed,
            "pressure_hpa": pressure,
            "should_alert": prob_6h >= 0.5,
        }
