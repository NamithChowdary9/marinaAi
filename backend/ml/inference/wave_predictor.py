"""
Wave Height Prediction — ML inference module.
Uses a trained LSTM/XGBoost ensemble model.
Falls back to physics-based estimation if no trained model is found.
"""

import numpy as np
import os
import joblib
from loguru import logger
from typing import Optional

from config.settings import settings


class WavePredictor:
    """
    Predicts future wave heights given atmospheric inputs.
    
    Inputs:
        - wind_speed (km/h)
        - pressure (hPa)
        - humidity (%)
        - temperature (°C)
        - current_wave_height (m)
    
    Outputs:
        - predicted wave height at 6h, 24h, 72h
        - confidence score
    """

    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        model_path = os.path.join(settings.ml_models_dir, "wave_prediction_model.pkl")
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                logger.info("Wave prediction model loaded")
            except Exception as e:
                logger.warning(f"Could not load wave model: {e}")
        else:
            logger.info("No saved wave model found — using physics-based estimation")

    def predict(
        self,
        wind_speed: float,
        pressure: float,
        humidity: float,
        temperature: float,
        current_wave_height: float,
    ) -> dict:
        """Predict wave heights at 6h, 24h, 72h intervals."""
        features = np.array([[
            wind_speed, pressure, humidity, temperature, current_wave_height
        ]])

        if self.model is not None:
            try:
                prediction = self.model.predict(features)
                return {
                    "6h":  round(float(prediction[0][0]), 2),
                    "24h": round(float(prediction[0][1]), 2),
                    "72h": round(float(prediction[0][2]), 2),
                    "confidence": 0.85,
                    "model": "trained_ml",
                }
            except Exception as e:
                logger.warning(f"Model inference failed: {e}")

        # Physics-based fallback (Beaufort scale approximation)
        return self._physics_estimate(wind_speed, current_wave_height, pressure)

    def _physics_estimate(
        self, wind_speed: float, current_wave: float, pressure: float
    ) -> dict:
        """
        Empirical wave height estimation using simplified JONSWAP model.
        Wave height ≈ 0.0248 × wind_speed^2 (in deep water, fetch-unlimited)
        """
        wind_ms = wind_speed / 3.6
        # Simplified significant wave height formula
        hs = 0.0248 * (wind_ms ** 2)
        # Pressure correction — low pressure = higher waves
        pressure_factor = max(0.8, min(1.2, (1013 - pressure) / 30 + 1.0))
        hs *= pressure_factor

        # Blend with current observed wave height
        base = (hs * 0.6 + current_wave * 0.4)

        # Apply time damping/growth
        h_6h  = round(base * 1.05, 2)
        h_24h = round(base * 0.95, 2)
        h_72h = round(base * 0.90, 2)

        return {
            "6h":  max(0.1, h_6h),
            "24h": max(0.1, h_24h),
            "72h": max(0.1, h_72h),
            "confidence": 0.60,
            "model": "physics_based",
        }
