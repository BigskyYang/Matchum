
from typing import Any, Dict

SEX_MAP = {"남성":1, "여성":2}
DRINK_FREQ_ORD_MAP = {"최근 1년간 마시지 않음":0, "월 1회 미만":1, "월 1회 정도":2, "월 2~4회":3, "주 2~3회":4, "주 4회 이상":5}
DRINK_AMOUNT_ORD_MAP = {"1~2잔":1, "3~4잔":2, "5~6잔":3, "7~9잔":4, "10잔 이상":5}
STRENGTH_DAYS_MAP = {"0일":0, "1일":1, "2일":2, "3일":3, "4일":4, "5일 이상":5}
STRESS_MAP = {"대단히 많이 느낀다":1, "많이 느끼는 편이다":1, "조금 느끼는 편이다":0, "거의 느끼지 않는다":0}
MEAL_FREQ_ORD_MAP = {"주 5~7회":3, "주 3~4회":2, "주 1~2회":1, "주 0회":0}
EATINGOUT_FREQ_ORD_MAP = {"하루 2회 이상":6, "하루 1회":5, "주 5~6회":4, "주 3~4회":3, "주 1~2회":2, "월 1~3회":1, "거의 안 함":0}
FRUIT_VEG_FREQ_MAP = {"하루 3회 이상":1, "하루 2회":2, "하루 1회":3, "주 5~6회":4, "주 2~4회":5, "주 1회":6, "월 2~3회":7, "월 1회":8, "거의 안 함":9}

def _require(d,key):
    if key not in d or d[key] is None:
        raise ValueError(f"Missing required survey field: {key}")
    return d[key]

def _choice(v,m,key):
    if v not in m:
        raise ValueError(f"Unexpected answer for {key}: {v!r}")
    return m[v]

def _mins(h,m):
    h=float(h); m=float(m)
    if not (0<=h<=168 and 0<=m<60):
        raise ValueError("Duration requires nonnegative hours and minutes 0..59")
    return h*60 + m

def _time_minutes(t):
    h,m=map(int,t.split(":"))
    if not (0<=h<=23 and 0<=m<=59):
        raise ValueError(f"Invalid HH:MM: {t}")
    return h*60+m

def _sleep(bed,wake):
    b=_time_minutes(bed); w=_time_minutes(wake)
    if w<=b: w+=1440
    return (w-b)/60

def preprocess_survey_response(s):
    sex=_choice(_require(s,"sex"),SEX_MAP,"sex")
    age=float(_require(s,"age"))
    if not (19 <= age <= 120) or not age.is_integer():
        raise ValueError("age must be a whole number between 19 and 120")

    smoking=_require(s,"currently_smoking")
    if type(smoking) is not bool:
        raise ValueError("currently_smoking must be boolean")
    smoker=int(smoking)
    cig=float(_require(s,"cigarettes_per_day")) if smoking else 0.0

    ever=_require(s,"ever_drink")
    if type(ever) is not bool:
        raise ValueError("ever_drink must be boolean")
    if not ever:
        drink_month=0; drink_freq=0; drink_amount=0
    else:
        freq=_require(s,"drink_frequency")
        drink_freq=_choice(freq,DRINK_FREQ_ORD_MAP,"drink_frequency")
        drink_month=int(drink_freq>=2)
        # Monthly drinking and amount per occasion are separate training features.
        # A person drinking less than monthly still has a nonzero amount code.
        drink_amount=0 if drink_freq==0 else _choice(_require(s,"drink_amount"),DRINK_AMOUNT_ORD_MAP,"drink_amount")

    active=_require(s,"aerobic_150min")
    if type(active) is not bool:
        raise ValueError("aerobic_150min must be boolean")
    aerobic=int(active)

    regular=_require(s,"regular_sleep_schedule")
    if type(regular) is not bool:
        raise ValueError("regular_sleep_schedule must be boolean")
    if regular:
        work_sleep=_sleep(_require(s,"workday_bedtime"),_require(s,"workday_waketime"))
        rest_sleep=_sleep(_require(s,"restday_bedtime"),_require(s,"restday_waketime"))
        sleep=(work_sleep*5+rest_sleep*2)/7
    else:
        sleep=float(_require(s,"average_sleep_hours"))

    model_features={
        "설명_sex":sex,
        "설명_age":age,
        "ML_smoker":smoker,
        "ML_cigarettes_day":cig,
        "ML_drink_month":drink_month,
        "ML_drink_freq_ord":drink_freq,
        "ML_drink_amount_ord":drink_amount,
        "ML_aerobic":aerobic,
        "ML_strength_days":_choice(_require(s,"strength_days"),STRENGTH_DAYS_MAP,"strength_days"),
        "ML_sedentary_min":_mins(s.get("sedentary_hours",0) or 0,s.get("sedentary_minutes",0) or 0),
        "ML_sleep_hours":sleep,
        "ML_stress":_choice(_require(s,"stress"),STRESS_MAP,"stress"),
        "ML_breakfast_freq_ord":_choice(_require(s,"breakfast_frequency"),MEAL_FREQ_ORD_MAP,"breakfast_frequency"),
        "ML_lunch_freq_ord":_choice(_require(s,"lunch_frequency"),MEAL_FREQ_ORD_MAP,"lunch_frequency"),
        "ML_dinner_freq_ord":_choice(_require(s,"dinner_frequency"),MEAL_FREQ_ORD_MAP,"dinner_frequency"),
        "ML_eatingout_freq_ord":_choice(_require(s,"eatingout_frequency"),EATINGOUT_FREQ_ORD_MAP,"eatingout_frequency"),
        "식습관_LS_FRUIT":_choice(_require(s,"fruit_frequency"),FRUIT_VEG_FREQ_MAP,"fruit_frequency"),
        "식습관_LS_VEG2":_choice(_require(s,"vegetable_frequency"),FRUIT_VEG_FREQ_MAP,"vegetable_frequency"),
    }

    from .validation import validate_service_features
    return {"model_features":validate_service_features(model_features)}
