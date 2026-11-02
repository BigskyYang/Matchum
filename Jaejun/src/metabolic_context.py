
"""
Metabolic-health descriptive context.

These variables do NOT enter the nutrition prediction model.
They are used only to contextualize and prioritize interpretation.
"""

from typing import Dict, Any

def summarize_metabolic_context(
    hypertension: bool | None,
    diabetes: bool | None,
    dyslipidemia: bool | None,
) -> Dict[str, Any]:

    conditions = []
    if hypertension is True:
        conditions.append("hypertension")
    if diabetes is True:
        conditions.append("diabetes")
    if dyslipidemia is True:
        conditions.append("dyslipidemia")

    known = [x for x in [hypertension, diabetes, dyslipidemia] if x is not None]

    if len(known) == 0:
        burden = "unknown"
    elif len(conditions) == 0:
        burden = "none_reported"
    elif len(conditions) == 1:
        burden = "one_condition"
    else:
        burden = "multiple_conditions"

    interpretation_priorities = []
    if hypertension is True:
        interpretation_priorities += ["sodium_excess", "potassium", "fiber"]
    if diabetes is True:
        interpretation_priorities += ["fiber", "overall_diet_pattern"]
    if dyslipidemia is True:
        interpretation_priorities += ["fiber", "overall_diet_pattern"]

    # preserve order, remove duplicates
    interpretation_priorities = list(dict.fromkeys(interpretation_priorities))

    return {
        "hypertension_diagnosed": hypertension,
        "diabetes_diagnosed": diabetes,
        "dyslipidemia_diagnosed": dyslipidemia,
        "condition_count": len(conditions),
        "conditions": conditions,
        "burden": burden,
        "interpretation_priorities": interpretation_priorities,
        "usage": "descriptive_context_only",
        "nutrition_model_predictor": False,
    }
