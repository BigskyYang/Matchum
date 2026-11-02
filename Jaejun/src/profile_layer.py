
"""
Combined non-predictive profile layer.
"""

from typing import Dict, Any
from .mental_health import summarize_phq9
from .metabolic_context import summarize_metabolic_context

def build_profile_summary(profile_features: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "mental_health": summarize_phq9(profile_features.get("phq9")),
        "metabolic_health": summarize_metabolic_context(
            profile_features.get("hypertension_diagnosed"),
            profile_features.get("diabetes_diagnosed"),
            profile_features.get("dyslipidemia_diagnosed"),
        ),
        "work_pattern": {
            "shift_work": profile_features.get("shift_work"),
            "usage": "lifestyle_description_only",
            "nutrition_model_predictor": False,
        },
    }
