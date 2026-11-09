
"""
Mini-FFQ habitual nutrient-risk module, frozen v1.2 weights / v1.4 web adapter.

Validated on KNHANES FFQ:
- train: 2012-2015
- independent validation: 2016
- age: 19-64
- 5 habitual food-frequency groups
- 10 nutrient-risk outputs using 2025 KDRI-compatible thresholds

The model was frozen for this project; this is not a government certification.
The v1.4 release retains mini-FFQ weights; only lifestyle models were retrained.
"""

from pathlib import Path
import json, joblib
import pandas as pd
from .predict import _load_model

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/"config/mini_ffq_manifest.json").read_text(encoding="utf-8"))

FOOD_FREQ_ORD={
    "거의 먹지 않음":0,
    "월 1~3회":1,
    "주 1~2회":2,
    "주 3~4회":3,
    "주 5~6회":4,
    "하루 1회":5,
    "하루 2회":6,
    "하루 3회 이상":7,
}

def _ord(v):
    if v not in FOOD_FREQ_ORD:
        raise ValueError(f"Unknown food-frequency answer: {v!r}")
    return FOOD_FREQ_ORD[v]

def build_mini_ffq_features(survey):
    if survey.get("sex") not in ("남성", "여성"):
        raise ValueError("sex must be 남성 or 여성")
    age=float(survey["age"])
    if not 19 <= age <= 64 or not age.is_integer():
        raise ValueError("Mini-FFQ is supported only for ages 19..64")
    return {
        "sex": 1 if survey["sex"]=="남성" else 2,
        "age": float(survey["age"]),
        "meat_ord": _ord(survey["meat_frequency"]),
        "fish_ord": _ord(survey["fish_frequency"]),
        "egg_ord": _ord(survey["egg_frequency"]),
        "legume_ord": _ord(survey["legume_frequency"]),
        "dairy_ord": _ord(survey["dairy_frequency"]),
    }

def predict_mini_ffq(survey):
    x=build_mini_ffq_features(survey)
    X=pd.DataFrame([x])
    out={}
    for nutrient,meta in MANIFEST.items():
        model=_load_model(str(ROOT/meta["model_path"]))
        out[nutrient]=float(model.predict_proba(X[meta["features"]])[:,1][0])
    return out
