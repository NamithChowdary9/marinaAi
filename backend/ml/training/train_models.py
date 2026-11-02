"""
MarineAI — Train wave, storm, and collision ML models.
Run: python3 train_models.py
Saves trained .pkl files to ml/models/
"""

import os, sys
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, roc_auc_score, classification_report

# Paths
BASE  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA  = os.path.join(BASE, "data")
MDLS  = os.path.join(BASE, "models")
os.makedirs(MDLS, exist_ok=True)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def load(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        print(f"  ⚠ {name} not found — generating datasets first...")
        sys.path.insert(0, DATA)
        import generate_datasets
        generate_datasets.gen_wave_data()
        generate_datasets.gen_storm_data()
        generate_datasets.gen_collision_data()
    return pd.read_csv(path)

def save(obj, name):
    path = os.path.join(MDLS, name)
    joblib.dump(obj, path)
    size = os.path.getsize(path) / 1024
    print(f"  💾 Saved {name} ({size:.0f} KB)")


# ─── Wave prediction model ────────────────────────────────────────────────────

def train_wave():
    print("\n🌊 Training wave height predictor...")
    df = load("wave_training.csv")

    features = ["wind_speed_knots", "wind_direction_deg", "pressure_hpa",
                "fetch_km", "swell_period_s", "latitude", "longitude", "month"]
    targets  = ["wave_height_6h", "wave_height_24h", "wave_height_72h"]

    X = df[features].values
    y = df[targets].values

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.15, random_state=42)

    # Multi-output: train one GBR per horizon
    models = []
    for i, col in enumerate(targets):
        m = Pipeline([
            ("scaler", StandardScaler()),
            ("gbr", GradientBoostingRegressor(
                n_estimators=200, max_depth=5, learning_rate=0.08,
                subsample=0.85, min_samples_leaf=10, random_state=42
            ))
        ])
        m.fit(X_tr, y_tr[:, i])
        mae = mean_absolute_error(y_te[:, i], m.predict(X_te))
        print(f"  {col}: MAE = {mae:.3f} m")
        models.append(m)

    save(models, "wave_prediction_model.pkl")
    print("  ✅ Wave model saved")
    return models


# ─── Storm prediction model ───────────────────────────────────────────────────

def train_storm():
    print("\n⛈  Training storm predictor...")
    df = load("storm_training.csv")

    features = ["pressure_hpa", "wind_speed_knots", "wave_height_m",
                "humidity_pct", "temp_c", "latitude", "month", "pressure_tendency_hpa"]
    X = df[features].values
    y_prob  = df["storm_probability"].values
    y_label = df["storm_label"].values

    X_tr, X_te, yp_tr, yp_te, yl_tr, yl_te = train_test_split(
        X, y_prob, y_label, test_size=0.15, random_state=42
    )

    # Classifier (for predict_proba)
    clf = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", GradientBoostingClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.08,
            subsample=0.85, min_samples_leaf=8, random_state=42
        ))
    ])
    clf.fit(X_tr, yl_tr)
    proba = clf.predict_proba(X_te)[:, 1]
    auc   = roc_auc_score(yl_te, proba)
    print(f"  AUC-ROC = {auc:.4f}")
    print(classification_report(yl_te, clf.predict(X_te), target_names=["No storm","Storm"]))

    save(clf, "storm_prediction_model.pkl")
    print("  ✅ Storm model saved")
    return clf


# ─── Collision risk model ──────────────────────────────────────────────────────

def train_collision():
    print("\n⚓ Training collision risk predictor...")
    df = load("collision_training.csv")

    features = ["cpa_nm", "tcpa_minutes", "speed_a_knots", "speed_b_knots",
                "course_diff_deg", "visibility_nm", "traffic_density"]
    X = df[features].values
    y_score = df["risk_score"].values
    y_label = df["collision_label"].values

    X_tr, X_te, ys_tr, ys_te, yl_tr, yl_te = train_test_split(
        X, y_score, y_label, test_size=0.15, random_state=42
    )

    # Regressor for continuous risk score
    reg = Pipeline([
        ("scaler", StandardScaler()),
        ("gbr", GradientBoostingRegressor(
            n_estimators=200, max_depth=4, learning_rate=0.08,
            subsample=0.85, min_samples_leaf=8, random_state=42
        ))
    ])
    reg.fit(X_tr, ys_tr)
    mae = mean_absolute_error(ys_te, reg.predict(X_te))
    print(f"  Risk score MAE = {mae:.4f}")

    # Classifier for high/low risk binary
    clf = Pipeline([
        ("scaler", StandardScaler()),
        ("rf", RandomForestClassifier(
            n_estimators=200, max_depth=6, min_samples_leaf=5,
            class_weight="balanced", random_state=42
        ))
    ])
    clf.fit(X_tr, yl_tr)
    auc = roc_auc_score(yl_te, clf.predict_proba(X_te)[:, 1])
    print(f"  Classifier AUC-ROC = {auc:.4f}")

    save((reg, clf), "collision_prediction_model.pkl")
    print("  ✅ Collision model saved")
    return reg, clf


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  MarineAI — Model Training Pipeline")
    print("=" * 55)
    train_wave()
    train_storm()
    train_collision()
    print("\n✅ All models trained and saved to ml/models/")
    print("=" * 55)
