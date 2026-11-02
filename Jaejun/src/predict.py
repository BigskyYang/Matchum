import joblib
import pandas as pd
from .config import FEATURES, MODEL_DIR, MODEL_MANIFEST, RISK_THRESHOLDS

def _risk_band(nutrient: str, p: float) -> str:
    cuts = RISK_THRESHOLDS[nutrient]
    if p < cuts["low_mid"]:
        return "Low"
    if p < cuts["mid_high"]:
        return "Mid"
    return "High"

def predict_feature_row(feature_row: dict) -> dict:
    """
    Predict 14 nutrient intake-risk outputs from a PREPROCESSED research feature row.

    Important:
    - HEI_PROTF / HEI_DAIRY are KNHANES-derived training-side variables.
    - Do not directly substitute web-survey weekly servings until the survey-to-training
      calibration step is validated.
    """
    missing = [f for f in FEATURES if f not in feature_row]
    if missing:
        raise ValueError(f"Missing features: {missing}")

    X = pd.DataFrame([{f: feature_row[f] for f in FEATURES}])
    out = {}
    for nutrient, meta in MODEL_MANIFEST.items():
        model = joblib.load(MODEL_DIR / f"{nutrient}.joblib")
        p = float(model.predict_proba(X)[0, 1])
        out[nutrient] = {"probability": p, "risk_band": _risk_band(nutrient, p)}
    return out
