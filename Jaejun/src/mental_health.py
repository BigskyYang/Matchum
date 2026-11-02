
"""
Mental-health interpretation layer.

This module does NOT feed PHQ-9 into the nutrition prediction model.
It summarizes PHQ-9 separately for descriptive/profile use.

Safety:
PHQ-9 item 9 is treated as a safety flag. If item 9 > 0, the product
should not simply continue with nutrition feedback without an appropriate
safety response and support guidance.
"""

from typing import Dict, Any, List

def summarize_phq9(phq9: List[int] | None) -> Dict[str, Any]:
    if phq9 is None:
        return {
            "available": False,
            "total": None,
            "severity": None,
            "screen_positive_10plus": None,
            "item9_positive": None,
            "safety_flag": None,
        }

    if len(phq9) != 9:
        raise ValueError("PHQ-9 must contain exactly 9 items.")
    vals = [int(x) for x in phq9]
    if any(x < 0 or x > 3 for x in vals):
        raise ValueError("Each PHQ-9 item must be coded 0-3.")

    total = sum(vals)

    if total <= 4:
        severity = "minimal"
    elif total <= 9:
        severity = "mild"
    elif total <= 14:
        severity = "moderate"
    elif total <= 19:
        severity = "moderately_severe"
    else:
        severity = "severe"

    item9_positive = vals[8] > 0

    return {
        "available": True,
        "total": total,
        "severity": severity,
        "screen_positive_10plus": total >= 10,
        "item9_positive": item9_positive,
        "safety_flag": item9_positive,
        "usage": "descriptive_profile_only",
        "nutrition_model_predictor": False,
    }
