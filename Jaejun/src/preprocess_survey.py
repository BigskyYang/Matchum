
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

try:
    from .food_bridge import bridge_food_questions
except ImportError:
    from food_bridge import bridge_food_questions


# -----------------------------
# Generic helpers
# -----------------------------

def _require(d: Dict[str, Any], key: str) -> Any:
    if key not in d or d[key] is None:
        raise ValueError(f"Missing required survey field: {key}")
    return d[key]


def _choice(value: Any, mapping: Dict[str, Any], field: str):
    if value not in mapping:
        raise ValueError(
            f"Unexpected answer for {field}: {value!r}. "
            f"Allowed: {list(mapping.keys())}"
        )
    return mapping[value]


def _time_to_minutes(t: str) -> int:
    """Convert HH:MM to minutes from 00:00."""
    try:
        h, m = map(int, t.split(":"))
    except Exception:
        raise ValueError(f"Invalid time format {t!r}; expected HH:MM")
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"Invalid time value: {t!r}")
    return h * 60 + m


def sleep_duration_hours(bed: str, wake: str) -> float:
    """
    Calculate sleep duration from HH:MM strings.
    Handles crossing midnight.
    """
    b = _time_to_minutes(bed)
    w = _time_to_minutes(wake)
    if w <= b:
        w += 24 * 60
    return (w - b) / 60.0


def weighted_sleep_hours(work_bed: str, work_wake: str,
                         rest_bed: str, rest_wake: str) -> float:
    """
    5:2 weighted average sleep duration.
    """
    work = sleep_duration_hours(work_bed, work_wake)
    rest = sleep_duration_hours(rest_bed, rest_wake)
    return (work * 5 + rest * 2) / 7.0


def duration_minutes(hours: float, minutes: float) -> float:
    return float(hours) * 60 + float(minutes)


def aerobic_flag(moderate_minutes: float, vigorous_minutes: float) -> int:
    """
    Current internal rule:
    moderate + 2*vigorous >= 150 min/week
    """
    return int(float(moderate_minutes) + 2 * float(vigorous_minutes) >= 150)


# -----------------------------
# Survey coding maps
# -----------------------------

SEX_MAP = {
    "남성": 1,
    "여성": 2,
}

CURRENT_SMOKING_MAP = {
    "매일 피움": 1,
    "가끔 피움": 1,
    "과거에는 피웠으나 현재는 피우지 않음": 0,
}

# ML_drink_month: any alcohol use in the past year
DRINK_MONTH_MAP = {
    "최근 1년간 마시지 않음": 0,
    "월 1회 미만": 1,
    "월 1회 정도": 1,
    "월 2~4회": 1,
    "주 2~3회": 1,
    "주 4회 이상": 1,
}

# Ordinal coding: higher = more frequent.
DRINK_FREQ_ORD_MAP = {
    "최근 1년간 마시지 않음": 0,
    "월 1회 미만": 1,
    "월 1회 정도": 2,
    "월 2~4회": 3,
    "주 2~3회": 4,
    "주 4회 이상": 5,
}

DRINK_AMOUNT_ORD_MAP = {
    "1~2잔": 1,
    "3~4잔": 2,
    "5~6잔": 3,
    "7~9잔": 4,
    "10잔 이상": 5,
}

STRENGTH_DAYS_MAP = {
    "0일": 0,
    "1일": 1,
    "2일": 2,
    "3일": 3,
    "4일": 4,
    "5일 이상": 5,
}

# Existing modeling convention: 1 = high stress, 0 = lower stress.
STRESS_MAP = {
    "대단히 많이 느낀다": 1,
    "많이 느끼는 편이다": 1,
    "조금 느끼는 편이다": 0,
    "거의 느끼지 않는다": 0,
}

# Meal frequency coding: lower value = more regular/frequent.
MEAL_FREQ_ORD_MAP = {
    "주 5~7회": 1,
    "주 3~4회": 2,
    "주 1~2회": 3,
    "주 0회": 4,
}

# Eating-out coding: lower value = more frequent.
EATINGOUT_FREQ_ORD_MAP = {
    "하루 2회 이상": 1,
    "하루 1회": 2,
    "주 5~6회": 3,
    "주 3~4회": 4,
    "주 1~2회": 5,
    "월 1~3회": 6,
    "거의 안 함": 7,
}

# KNHANES-style categorical frequency codes used in the current model.
# Higher code = less frequent intake.
FRUIT_FREQ_MAP = {
    "하루 3회 이상": 1,
    "하루 2회": 2,
    "하루 1회": 3,
    "주 5~6회": 4,
    "주 2~4회": 5,
    "주 1회": 6,
    "월 2~3회": 7,
    "월 1회": 8,
    "거의 안 함": 9,
}

VEG_FREQ_MAP = FRUIT_FREQ_MAP.copy()

# User-friendly frequency -> approximate servings/day.
# IMPORTANT: These are NOT HEI_PROTF / HEI_DAIRY.
FOOD_SERVING_DAY_MAP = {
    "거의 먹지 않음": 0.0,
    "주 1~2회": 1.5 / 7,
    "주 3~4회": 3.5 / 7,
    "주 5~7회": 6.0 / 7,
    "하루 1회": 1.0,
    "하루 1회 정도": 1.0,
    "하루 2회": 2.0,
    "하루 2회 정도": 2.0,
    "하루 3회 이상": 3.0,
    "하루 2회 이상": 2.0,
}


# -----------------------------
# Main preprocessing function
# -----------------------------

def preprocess_survey_response(survey: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert raw questionnaire responses into the research-model feature format.

    Returns:
      {
        "model_features": {...},
        "bridge_features": {...},
        "profile_features": {...},
        "warnings": [...]
      }

    Notes:
    - model_features intentionally excludes HEI_PROTF / HEI_DAIRY because
      current web survey frequencies are not identical to the KNHANES-derived
      HEI variables used at training time.
    - bridge_features contains approximate servings/day for Q25/Q26.
    """

    warnings = []

    # Basic
    sex = _choice(_require(survey, "sex"), SEX_MAP, "sex")
    age = float(_require(survey, "age"))

    # Smoking
    lifetime_100 = bool(_require(survey, "smoked_100_cigarettes"))
    if not lifetime_100:
        smoker = 0
        cigarettes_day = 0.0
    else:
        current_smoking = _require(survey, "current_smoking")
        smoker = _choice(current_smoking, CURRENT_SMOKING_MAP, "current_smoking")
        cigarettes_day = float(survey.get("cigarettes_per_day", 0) or 0)
        if smoker == 0:
            cigarettes_day = 0.0

    # Alcohol
    ever_drink = bool(_require(survey, "ever_drink"))
    if not ever_drink:
        drink_month = 0
        drink_freq_ord = 0
        drink_amount_ord = 0
    else:
        drink_freq = _require(survey, "drink_frequency")
        drink_month = _choice(drink_freq, DRINK_MONTH_MAP, "drink_frequency")
        drink_freq_ord = _choice(drink_freq, DRINK_FREQ_ORD_MAP, "drink_frequency")

        if drink_month == 0:
            drink_amount_ord = 0
        else:
            drink_amount = _require(survey, "drink_amount")
            drink_amount_ord = _choice(
                drink_amount, DRINK_AMOUNT_ORD_MAP, "drink_amount"
            )

    # Physical activity
    mod_min = duration_minutes(
        float(survey.get("moderate_hours", 0) or 0),
        float(survey.get("moderate_minutes", 0) or 0),
    )
    vig_min = duration_minutes(
        float(survey.get("vigorous_hours", 0) or 0),
        float(survey.get("vigorous_minutes", 0) or 0),
    )
    aerobic = aerobic_flag(mod_min, vig_min)
    strength_days = _choice(
        _require(survey, "strength_days"),
        STRENGTH_DAYS_MAP,
        "strength_days",
    )

    # Sedentary
    sedentary_min = duration_minutes(
        float(survey.get("sedentary_hours", 0) or 0),
        float(survey.get("sedentary_minutes", 0) or 0),
    )

    # Sleep
    sleep_hours = weighted_sleep_hours(
        _require(survey, "workday_bedtime"),
        _require(survey, "workday_waketime"),
        _require(survey, "restday_bedtime"),
        _require(survey, "restday_waketime"),
    )

    # Stress
    stress = _choice(_require(survey, "stress"), STRESS_MAP, "stress")

    # Meals
    breakfast = _choice(
        _require(survey, "breakfast_frequency"),
        MEAL_FREQ_ORD_MAP,
        "breakfast_frequency",
    )
    lunch = _choice(
        _require(survey, "lunch_frequency"),
        MEAL_FREQ_ORD_MAP,
        "lunch_frequency",
    )
    dinner = _choice(
        _require(survey, "dinner_frequency"),
        MEAL_FREQ_ORD_MAP,
        "dinner_frequency",
    )
    eatingout = _choice(
        _require(survey, "eatingout_frequency"),
        EATINGOUT_FREQ_ORD_MAP,
        "eatingout_frequency",
    )

    # Fruit / vegetables
    fruit = _choice(
        _require(survey, "fruit_frequency"),
        FRUIT_FREQ_MAP,
        "fruit_frequency",
    )
    veg = _choice(
        _require(survey, "vegetable_frequency"),
        VEG_FREQ_MAP,
        "vegetable_frequency",
    )

    # Food-group bridge values
    protf_servings_day = _choice(
        _require(survey, "protein_food_frequency"),
        FOOD_SERVING_DAY_MAP,
        "protein_food_frequency",
    )
    dairy_servings_day = _choice(
        _require(survey, "dairy_frequency"),
        FOOD_SERVING_DAY_MAP,
        "dairy_frequency",
    )

    warnings.append(
        "protein_food_servings_day / dairy_servings_day are approximate survey-side "
        "bridge values and must not be treated as HEI_PROTF / HEI_DAIRY without "
        "calibration."
    )

    model_features = {
        "설명_sex": sex,
        "설명_age": age,
        "ML_smoker": smoker,
        "ML_cigarettes_day": cigarettes_day,
        "ML_drink_month": drink_month,
        "ML_drink_freq_ord": drink_freq_ord,
        "ML_drink_amount_ord": drink_amount_ord,
        "ML_aerobic": aerobic,
        "ML_strength_days": strength_days,
        "ML_sedentary_min": sedentary_min,
        "ML_sleep_hours": sleep_hours,
        "ML_stress": stress,
        "ML_breakfast_freq_ord": breakfast,
        "ML_lunch_freq_ord": lunch,
        "ML_dinner_freq_ord": dinner,
        "ML_eatingout_freq_ord": eatingout,
        "식습관_LS_FRUIT": fruit,
        "식습관_LS_VEG2": veg,
    }

    bridge_features = {
        "protein_food_servings_day": protf_servings_day,
        "dairy_servings_day": dairy_servings_day,
    }

    # Non-predictor contextual layers
    profile_features = {
        "shift_work": survey.get("shift_work"),
        "phq9": survey.get("phq9"),
        "hypertension_diagnosed": survey.get("hypertension_diagnosed"),
        "diabetes_diagnosed": survey.get("diabetes_diagnosed"),
        "dyslipidemia_diagnosed": survey.get("dyslipidemia_diagnosed"),
    }

    # Prototype v1 bridge:
    # Convert the survey-side food frequencies to approximate KHEI-compatible
    # 0-10 scores using the official proportional scoring rule.
    bridge_scores = bridge_food_questions(
        sex_code=sex,
        age=age,
        protein_food_frequency=_require(survey, "protein_food_frequency"),
        dairy_frequency=_require(survey, "dairy_frequency"),
    )

    model_features_with_bridge = dict(model_features)
    model_features_with_bridge["HEI_PROTF"] = bridge_scores["HEI_PROTF"]
    model_features_with_bridge["HEI_DAIRY"] = bridge_scores["HEI_DAIRY"]

    bridge_features.update({
        "HEI_PROTF_bridge_v1": bridge_scores["HEI_PROTF"],
        "HEI_DAIRY_bridge_v1": bridge_scores["HEI_DAIRY"],
        "bridge_method": bridge_scores["_bridge_meta"]["method"],
        "bridge_assumption": bridge_scores["_bridge_meta"]["assumption"],
        "bridge_status": bridge_scores["_bridge_meta"]["production_status"],
    })

    warnings.append(
        "Bridge v1 now creates HEI_PROTF/HEI_DAIRY-compatible 0-10 scores using "
        "official KHEI proportional scoring. However, the survey asks habitual "
        "frequency rather than exact KDRI serving intake, so this remains a "
        "prototype approximation requiring external validation."
    )

    return {
        "model_features": model_features_with_bridge,
        "bridge_features": bridge_features,
        "profile_features": profile_features,
        "warnings": warnings,
    }


def attach_calibrated_food_features(
    preprocessed: Dict[str, Any],
    hei_protf: float,
    hei_dairy: float,
) -> Dict[str, Any]:
    """
    Attach calibrated training-compatible food-group variables AFTER
    an external calibration/bridge step has produced HEI-compatible values.
    """
    out = dict(preprocessed["model_features"])
    out["HEI_PROTF"] = float(hei_protf)
    out["HEI_DAIRY"] = float(hei_dairy)
    return out
