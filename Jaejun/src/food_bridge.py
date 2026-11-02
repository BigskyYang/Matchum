
"""
Survey food-frequency -> KHEI-compatible bridge v1

Purpose
-------
Convert user-friendly Q25/Q26 food-group frequency responses into approximate
0-10 score variables compatible in scale and interpretation with:
- HEI_PROTF
- HEI_DAIRY

Method
------
1) Convert frequency category -> approximate servings/day.
2) Apply official KHEI proportional scoring rule.
3) Cap at 10 points.

IMPORTANT LIMITATION
--------------------
The web survey asks habitual frequency, not exact KDRI serving-size intake.
Therefore this bridge assumes one reported eating occasion ~= one serving.
It is a transparent approximation for Prototype v1 and should be validated
against directly measured serving intake before production deployment.
"""

from typing import Dict, Any

FOOD_SERVING_DAY_MAP = {
    "거의 먹지 않음": 0.0,
    "주 1~2회": 1.5 / 7.0,
    "주 3~4회": 3.5 / 7.0,
    "주 5~7회": 6.0 / 7.0,
    "하루 1회": 1.0,
    "하루 1회 정도": 1.0,
    "하루 2회": 2.0,
    "하루 2회 정도": 2.0,
    "하루 3회 이상": 3.0,
    "하루 2회 이상": 2.0,
}

def frequency_to_servings_day(answer: str) -> float:
    if answer not in FOOD_SERVING_DAY_MAP:
        raise ValueError(
            f"Unknown food-frequency answer: {answer!r}. "
            f"Allowed: {list(FOOD_SERVING_DAY_MAP)}"
        )
    return float(FOOD_SERVING_DAY_MAP[answer])

def protf_max_servings(sex_code: int, age: float) -> float:
    """
    Official KHEI maximum-score serving criterion.

    sex_code:
      1 = male
      2 = female

    Criteria:
      male, 19-64: 5 servings/day
      female, 19-64: 4 servings/day
      male, >=65: 4 servings/day
      female, >=65: 2.5 servings/day
    """
    age = float(age)

    if sex_code == 1:
        return 5.0 if age < 65 else 4.0
    if sex_code == 2:
        return 4.0 if age < 65 else 2.5
    raise ValueError("sex_code must be 1 (male) or 2 (female)")

def score_protf(servings_day: float, sex_code: int, age: float) -> float:
    """
    HEI_PROTF-compatible 0-10 score approximation.
    Linear proportional scoring between 0 intake and maximum-score criterion.
    """
    max_serv = protf_max_servings(sex_code, age)
    score = 10.0 * max(float(servings_day), 0.0) / max_serv
    return min(score, 10.0)

def score_dairy(servings_day: float) -> float:
    """
    HEI_DAIRY-compatible 0-10 score approximation.
    Official maximum-score criterion = >= 1 serving/day.
    """
    score = 10.0 * max(float(servings_day), 0.0) / 1.0
    return min(score, 10.0)

def bridge_food_questions(
    sex_code: int,
    age: float,
    protein_food_frequency: str,
    dairy_frequency: str,
) -> Dict[str, Any]:
    protf_serv = frequency_to_servings_day(protein_food_frequency)
    dairy_serv = frequency_to_servings_day(dairy_frequency)

    return {
        "HEI_PROTF": score_protf(protf_serv, sex_code, age),
        "HEI_DAIRY": score_dairy(dairy_serv),
        "_bridge_meta": {
            "protein_food_servings_day": protf_serv,
            "dairy_servings_day": dairy_serv,
            "method": "KHEI proportional scoring bridge v1",
            "assumption": "1 reported eating occasion approximates 1 serving",
            "production_status": "prototype_requires_validation",
        },
    }
