
from .preprocess_survey import preprocess_survey_response
from .predict import predict_service_features
from .profile_layer import build_profile_summary

def predict_from_survey(survey):
    prepared=preprocess_survey_response(survey)
    return {
        "nutrition_predictions":predict_service_features(prepared["model_features"]),
        "nutrition_model_version":"service_survey_only_v1",
        "model_features":prepared["model_features"],
        "dietary_context":prepared["dietary_context"],
        "profile_summary":build_profile_summary(prepared["profile_features"]),
        "lifestyle_cluster":None,  # attach after final clustering model is frozen
    }
