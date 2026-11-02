
"""
v1.2 dual-signal service pipeline

Outputs two conceptually different signals:
1) lifestyle_risk: current 2022-2024 survey-only model
2) habitual_diet_risk: 2012-2016 mini-FFQ model

They are NOT averaged into one probability because the two modules were trained
on different cohorts and different target constructions.

The frontend may present them together, but must retain their labels.
"""

from .preprocess_survey import preprocess_survey_response
from .predict import predict_service_features
from .profile_layer import build_profile_summary
from .mini_ffq import predict_mini_ffq

def predict_from_survey_v1_2(survey):
    prepared = preprocess_survey_response(survey)

    lifestyle = predict_service_features(prepared["model_features"])

    mini_ffq_required = [
        "meat_frequency","fish_frequency","egg_frequency",
        "legume_frequency","dairy_frequency"
    ]
    has_all_ffq = all(survey.get(k) is not None for k in mini_ffq_required)

    habitual = predict_mini_ffq(survey) if has_all_ffq else None

    return {
        "version": "v1.2-dual-signal",
        "nutrition": {
            "lifestyle_risk": lifestyle,
            "habitual_diet_risk": habitual,
            "habitual_diet_available": has_all_ffq,
            "combination_policy": "do_not_average_probabilities",
        },
        "profile_summary": build_profile_summary(prepared["profile_features"]),
        "dietary_context": prepared["dietary_context"],
        "lifestyle_cluster": None,
    }
