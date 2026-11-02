
"""
Mini-FFQ habitual nutrient-risk candidate module (v1.2 candidate)

Validated on KNHANES FFQ:
- train: 2012-2015
- independent validation: 2016
- age: 19-64
- 5 habitual food-frequency groups
- 10 nutrient-risk outputs using 2025 KDRI-compatible thresholds

This module is NOT yet the official production model.
Final promotion requires same-dataset integration testing with historical ALL
files so lifestyle covariates and mini-FFQ incremental value can be tested together.
"""

from pathlib import Path
import json, joblib
import pandas as pd

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
        model=joblib.load(ROOT/meta["model_path"])
        out[nutrient]=float(model.predict_proba(X[meta["features"]])[:,1][0])
    return out
