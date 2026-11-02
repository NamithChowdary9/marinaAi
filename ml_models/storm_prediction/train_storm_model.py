"""
Storm Prediction Model Training Script
────────────────────────────────────────
Trains a GradientBoosting classifier to predict storm probability.

Usage:
    python train_storm_model.py

Output:
    Saves model to: backend/ml_models/saved/storm_prediction_model.pkl
"""

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, roc_auc_score
import joblib
import os

np.random.seed(42)
N = 15_000

# Features
pressure     = np.random.uniform(960, 1040, N)
temperature  = np.random.uniform(15, 35, N)
humidity     = np.random.uniform(40, 100, N)
wind_speed   = np.random.uniform(0, 120, N)
sst          = temperature + np.random.uniform(-3, 3, N)

# Labels: storm = 1 based on meteorological thresholds
storm = (
    (pressure < 990)                  |
    ((pressure < 1005) & (wind_speed > 50)) |
    ((humidity > 85) & (sst > 27) & (wind_speed > 40))
).astype(int)

# Add noise
flip = np.random.random(N) < 0.05
storm = np.where(flip, 1 - storm, storm)

X = np.column_stack([pressure, temperature, humidity, wind_speed, sst])
y = storm

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

model = GradientBoostingClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    random_state=42,
)
model.fit(X_train, y_train)

# ─── Evaluation ─────────────────────────────────────────────────────────────

y_pred_proba = model.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, y_pred_proba)
print(f"  Storm AUC-ROC: {auc:.3f}")
print(classification_report(y_test, model.predict(X_test), target_names=["No Storm", "Storm"]))

# ─── Save ────────────────────────────────────────────────────────────────────

output_dir = os.path.join(os.path.dirname(__file__), "../../backend/ml_models/saved")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "storm_prediction_model.pkl")
joblib.dump(model, output_path)
print(f"\n✅ Storm model saved to: {output_path}")
