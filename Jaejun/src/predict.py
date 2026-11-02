
import json, joblib
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
FEATURES=json.loads((ROOT/"config/service_features.json").read_text(encoding="utf-8"))
CUTS=json.loads((ROOT/"config/service_risk_thresholds.json").read_text(encoding="utf-8"))

def _band(n,p):
    c=CUTS[n]
    return "Low" if p<c["low_mid"] else ("Mid" if p<c["mid_high"] else "High")

def predict_service_features(feature_row):
    missing=[x for x in FEATURES if x not in feature_row]
    if missing: raise ValueError(f"Missing features: {missing}")
    X=pd.DataFrame([{f:feature_row[f] for f in FEATURES}])
    out={}
    for path in (ROOT/"models/service").glob("*.joblib"):
        n=path.stem
        model=joblib.load(path)
        p=float(model.predict_proba(X)[0,1])
        out[n]={"probability":p,"risk_band":_band(n,p)}
    return out
