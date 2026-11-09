"""Validate the training feature contract; unknown codes are never frequencies."""
import math

DISCRETE = {
    "설명_sex": {1, 2}, "ML_smoker": {0, 1}, "ML_drink_month": {0, 1},
    "ML_drink_freq_ord": set(range(6)), "ML_drink_amount_ord": set(range(6)),
    "ML_aerobic": {0, 1}, "ML_strength_days": set(range(6)), "ML_stress": {0, 1},
    "ML_breakfast_freq_ord": set(range(4)), "ML_lunch_freq_ord": set(range(4)),
    "ML_dinner_freq_ord": set(range(4)), "ML_eatingout_freq_ord": set(range(7)),
    "식습관_LS_FRUIT": set(range(1, 10)), "식습관_LS_VEG2": set(range(1, 10)),
}
CONTINUOUS = {"설명_age": (19, 120), "ML_cigarettes_day": (0, 200),
              "ML_sedentary_min": (0, 1440), "ML_sleep_hours": (0, 24)}

def validate_service_features(row):
    expected = set(DISCRETE) | set(CONTINUOUS)
    if set(row) != expected:
        raise ValueError(f"Feature keys mismatch; missing={sorted(expected-set(row))}, extra={sorted(set(row)-expected)}")
    out = {}
    for key, value in row.items():
        if isinstance(value, (bool, str)) or value is None:
            raise ValueError(f"{key}: a finite numeric training code is required")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError(f"{key}: missing/nonfinite values are not supported by this web contract")
        if key in DISCRETE and value not in DISCRETE[key]:
            raise ValueError(f"{key}: invalid code {value}; 99/unknown is not an answer")
        if key in CONTINUOUS:
            lo, hi = CONTINUOUS[key]
            if not lo <= value <= hi:
                raise ValueError(f"{key}: expected {lo}..{hi}")
        out[key] = value
    if not out["설명_age"].is_integer():
        raise ValueError("Age must be a whole number")
    if out["ML_drink_month"] != int(out["ML_drink_freq_ord"] >= 2):
        raise ValueError("ML_drink_month must equal int(ML_drink_freq_ord >= 2)")
    if (out["ML_drink_freq_ord"] == 0) != (out["ML_drink_amount_ord"] == 0):
        raise ValueError("Drink amount must be zero only for no drinking in the past year")
    if out["ML_smoker"] == 0 and out["ML_cigarettes_day"] != 0:
        raise ValueError("A nonsmoker must have ML_cigarettes_day=0")
    return out
