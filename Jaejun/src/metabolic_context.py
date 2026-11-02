
def summarize_metabolic_context(hypertension,diabetes,dyslipidemia):
    conditions=[]
    if hypertension is True: conditions.append("hypertension")
    if diabetes is True: conditions.append("diabetes")
    if dyslipidemia is True: conditions.append("dyslipidemia")
    priorities=[]
    if hypertension is True: priorities += ["sodium_excess","potassium","fiber"]
    if diabetes is True: priorities += ["fiber","overall_diet_pattern"]
    if dyslipidemia is True: priorities += ["fiber","overall_diet_pattern"]
    return {
        "conditions":conditions,
        "condition_count":len(conditions),
        "interpretation_priorities":list(dict.fromkeys(priorities)),
        "nutrition_model_predictor":False
    }
