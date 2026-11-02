
def summarize_phq9(phq9):
    if phq9 is None:
        return {"available":False}
    if len(phq9)!=9:
        raise ValueError("PHQ-9 must contain 9 items")
    vals=[int(x) for x in phq9]
    if any(x<0 or x>3 for x in vals):
        raise ValueError("PHQ-9 items must be 0-3")
    total=sum(vals)
    if total<=4: severity="minimal"
    elif total<=9: severity="mild"
    elif total<=14: severity="moderate"
    elif total<=19: severity="moderately_severe"
    else: severity="severe"
    return {
        "available":True,"total":total,"severity":severity,
        "screen_positive_10plus":total>=10,
        "item9_positive":vals[8]>0,
        "safety_flag":vals[8]>0,
        "nutrition_model_predictor":False
    }
