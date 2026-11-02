
"""
End-to-end prototype inference:
raw survey JSON -> preprocessing -> food bridge -> 14 nutrient predictions
"""

from typing import Dict, Any
from .preprocess_survey import preprocess_survey_response
from .predict import predict_feature_row
from .profile_layer import build_profile_summary

def predict_from_survey(survey: Dict[str, Any]) -> Dict[str, Any]:
    prepared = preprocess_survey_response(survey)
    predictions = predict_feature_row(prepared["model_features"])

    profile_summary = build_profile_summary(prepared["profile_features"])

    return {
        "predictions": predictions,
        "model_features": prepared["model_features"],
        "bridge_features": prepared["bridge_features"],
        "profile_features": prepared["profile_features"],
        "profile_summary": profile_summary,
        "warnings": prepared["warnings"],
    }
