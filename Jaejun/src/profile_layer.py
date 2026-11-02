
from .mental_health import summarize_phq9
from .metabolic_context import summarize_metabolic_context

def build_profile_summary(p):
    return {
        "mental_health":summarize_phq9(p.get("phq9")),
        "metabolic_health":summarize_metabolic_context(
            p.get("hypertension_diagnosed"),
            p.get("diabetes_diagnosed"),
            p.get("dyslipidemia_diagnosed"),
        ),
        "work_pattern":{
            "shift_work":p.get("shift_work"),
            "nutrition_model_predictor":False
        }
    }
