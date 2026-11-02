"""
Wave Height Prediction Model Training Script
─────────────────────────────────────────────
Trains an XGBoost model to predict wave heights at 6h, 24h, 72h horizons.

Usage:
    python train_wave_model.py

Output:
    Saves trained model to: backend/ml_models/saved/wave_prediction_model.pkl
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_squared_error
import xgboost as xgb
import joblib
import os

# ─── Synthetic Training Data ──────────────────────────────────────────────────
# In production: replace with real NOAA / ERA5 ocean dataset

np.random.seed(42)
N = 10_000

wind_speed   = np.random.uniform(0, 100, N)     # km/h
pressure     = np.random.uniform(960, 1040, N)  # hPa
humidity     = np.random.uniform(40, 100, N)    # %
temperature  = np.random.uniform(15, 35, N)     # °C
current_wave = np.random.uniform(0, 8, N)       # m

# Physics-inspired label generation (JONSWAP approximation)
wind_ms = wind_speed / 3.6
base_wave = 0.0248 * (wind_ms ** 2)
pressure_factor = np.clip((1013 - pressure) / 30 + 1.0, 0.7, 1.5)
base_wave *= pressure_factor

wave_6h  = np.clip(base_wave * 0.7 + current_wave * 0.3 + np.random.normal(0, 0.2, N), 0.1, 15)
wave_24h = np.clip(base_wave * 0.6 + current_wave * 0.25 + np.random.normal(0, 0.3, N), 0.1, 15)
wave_72h = np.clip(base_wave * 0.5 + current_wave * 0.2 + np.random.normal(0, 0.4, N), 0.1, 15)

X = np.column_stack([wind_speed, pressure, humidity, temperature, current_wave])
y = np.column_stack([wave_6h, wave_24h, wave_72h])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ─── Model ─────────────────────────────────────────────────────────────────────

base_xgb = xgb.XGBRegressor(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1,
)

model = MultiOutputRegressor(base_xgb)
model.fit(X_train, y_train)

# ─── Evaluation ───────────────────────────────────────────────────────────────

y_pred = model.predict(X_test)
for i, horizon in enumerate(["6h", "24h", "72h"]):
    rmse = np.sqrt(mean_squared_error(y_test[:, i], y_pred[:, i]))
    print(f"  Wave {horizon} RMSE: {rmse:.3f}m")

# ─── Save ─────────────────────────────────────────────────────────────────────

output_dir = os.path.join(os.path.dirname(__file__), "../../backend/ml_models/saved")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "wave_prediction_model.pkl")
joblib.dump(model, output_path)
print(f"\n✅ Wave model saved to: {output_path}")
