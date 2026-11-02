
"""
KNHANES Nutrition Service v1.2 FINAL

Architecture
------------
1) lifestyle_risk
   - official 2022-2024 survey-only model
   - 14 nutrient outputs

2) habitual_diet_risk
   - validated 2012-2016 mini-FFQ model
   - age 19-64 only
   - 10 nutrient outputs

3) profile layers
   - PHQ-9 mental-health profile
   - metabolic-health context
   - supplement safety gate
   - lifestyle cluster/NBTI hook

Important:
- lifestyle and habitual-diet probabilities are NOT averaged.
- habitual-diet module is unavailable for age >=65.
"""

from pathlib import Path
import json
from .preprocess_survey import preprocess_survey_response
from .predict import predict_service_features
from .profile_layer import build_profile_summary
from .mini_ffq import predict_mini_ffq

ROOT = Path(__file__).resolve().parents[1]
FFQ_THRESHOLDS = json.loads((ROOT/"config/mini_ffq_risk_thresholds.json").read_text(encoding="utf-8"))
SAFETY_RULES = json.loads((ROOT/"config/supplement_safety_rules.json").read_text(encoding="utf-8"))

def _band(prob, nutrient):
    th = FFQ_THRESHOLDS.get(nutrient)
    if th is None:
        return None
    if prob <= th["low_max"]:
        return "Low"
    if prob <= th["mid_max"]:
        return "Mid"
    return "High"

def _safety_gate(survey):
    flags = []
    blocked = False

    if survey.get("pregnant_or_breastfeeding") is True:
        blocked = True
        flags.append({
            "type":"pregnant_or_breastfeeding",
            **SAFETY_RULES["pregnant_or_breastfeeding"]
        })

    if survey.get("kidney_disease_or_stones") is True:
        flags.append({
            "type":"kidney_disease_or_stones",
            **SAFETY_RULES["kidney_disease_or_stones"]
        })

    if survey.get("anticoagulant_or_aspirin") is True:
        flags.append({
            "type":"anticoagulant_or_aspirin",
            **SAFETY_RULES["anticoagulant_or_aspirin"]
        })

    current = survey.get("current_supplements") or []
    if current:
        flags.append({
            "type":"current_supplements",
            "current_supplements":current,
            **SAFETY_RULES["current_supplements"]
        })

    return {
        "product_recommendation_blocked": blocked,
        "flags": flags
    }

def predict_from_survey_v1_2_final(survey):
    prepared = preprocess_survey_response(survey)
    lifestyle = predict_service_features(prepared["model_features"])

    age = float(survey["age"])
    ffq_keys = [
        "meat_frequency","fish_frequency","egg_frequency",
        "legume_frequency","dairy_frequency"
    ]
    has_all_ffq = all(survey.get(k) is not None for k in ffq_keys)
    age_supported = 19 <= age <= 64

    habitual = None
    habitual_bands = None
    fallback_reason = None

    if not age_supported:
        fallback_reason = "mini_ffq_validated_for_age_19_64_only"
    elif not has_all_ffq:
        fallback_reason = "mini_ffq_incomplete"
    else:
        habitual = predict_mini_ffq(survey)
        habitual_bands = {k:_band(v,k) for k,v in habitual.items()}

    safety = _safety_gate(survey)

    return {
        "version":"v1.2-final",
        "nutrition":{
            "lifestyle_risk": lifestyle,
            "habitual_diet_risk": habitual,
            "habitual_diet_risk_band": habitual_bands,
            "habitual_diet_available": habitual is not None,
            "habitual_diet_fallback_reason": fallback_reason,
            "combination_policy":"separate_signals_no_probability_averaging"
        },
        "profile_summary": build_profile_summary(prepared["profile_features"]),
        "dietary_context": prepared.get("dietary_context"),
        "lifestyle_cluster":{
            "status":"awaiting_final_cluster_mapping",
            "cluster_id":None,
            "cluster_name":None
        },
        "supplement_safety": safety
    }
