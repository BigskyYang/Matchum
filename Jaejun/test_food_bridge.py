
from src.food_bridge import (
    frequency_to_servings_day, score_protf, score_dairy
)

def test_dairy_one_serving_is_max():
    assert score_dairy(1.0) == 10.0

def test_dairy_zero():
    assert score_dairy(0.0) == 0.0

def test_protf_male_under65_max():
    assert score_protf(5.0, 1, 30) == 10.0

def test_protf_female_under65_max():
    assert score_protf(4.0, 2, 30) == 10.0

def test_protf_male_65plus_max():
    assert score_protf(4.0, 1, 70) == 10.0

def test_protf_female_65plus_max():
    assert score_protf(2.5, 2, 70) == 10.0

def test_weekly_mapping():
    assert abs(frequency_to_servings_day("주 3~4회") - 0.5) < 1e-9
