"""
Front-end survey conversion helpers.

This module converts questionnaire responses for variables that have a direct
one-to-one mapping to the research model.

Food-frequency note:
Q25/Q26 are user-friendly weekly-serving questions. The current research model
was trained with KNHANES HEI_PROTF / HEI_DAIRY derived variables, not these raw
survey serving values. Therefore the adapter intentionally DOES NOT map
Q25/Q26 directly to HEI_PROTF / HEI_DAIRY. A calibration/bridge model should be
validated before deployment.
"""

def aerobic_flag(moderate_minutes: float, vigorous_minutes: float) -> int:
    return int(moderate_minutes + 2 * vigorous_minutes >= 150)

def duration_minutes(hours: float, minutes: float) -> float:
    return hours * 60 + minutes

def weighted_sleep_hours(workday_hours: float, restday_hours: float) -> float:
    return (workday_hours * 5 + restday_hours * 2) / 7

def stress_binary(answer: str) -> int:
    return int(answer in {"대단히 많이", "많이"})

def food_frequency_to_servings_day(answer: str) -> float:
    mapping = {
        "거의 먹지 않음": 0.0,
        "주 1~2회": 1.5 / 7,
        "주 3~4회": 3.5 / 7,
        "주 5~7회": 6.0 / 7,
        "하루 1회": 1.0,
        "하루 2회": 2.0,
        "하루 3회 이상": 3.0,
        "하루 2회 이상": 2.0,
    }
    return mapping[answer]
