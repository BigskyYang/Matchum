# 유형 이름과 그 근거 (03_final.py가 이름에 쓴 특징이 실제 데이터와 맞는지 확인한다)
# claims: (변수, +1 높음 / -1 낮음) — 이름에 쓴 특징만 적는다
# 유형 ID는 가중 인원 많은 순 (k=7, 영역 가중치 없음 기준). 모델을 다시 학습하면 03_최종모델.md를 보고 다시 맞춘다.
NAMES = {
    'A': {'name': '집밥 절주형', 'claims': [('drink_freq', -1), ('breakfast', +1), ('eating_out', -1)]},
    'B': {'name': '아침 패스형', 'claims': [('breakfast', -1), ('veg', -1)]},
    'C': {'name': '밥 챙기는 애주가형', 'claims': [('drink_freq', +1), ('breakfast', +1)]},
    'D': {'name': '술·담배 동반형', 'claims': [('smoker', +1), ('drink_amount', +1)]},
    'E': {'name': '근력 운동형', 'claims': [('strength_days', +1), ('aerobic', +1)]},
    'F': {'name': '저녁 거르는 형', 'claims': [('dinner', -1), ('veg', -1)]},
    'G': {'name': '점심 거르는 형', 'claims': [('lunch', -1), ('veg', -1)]},
}

# 지연님 12개 유형 보완판 이름 (05_jiyeon_improved.py). ID = 대분류 코드(N 활동 적은·A 운동·S 스트레스·O 좌식·외식) + 세부 번호
# 세부 번호는 세분화 변수(지연님 SUB_PLAN) 첫째 → 둘째 값이 작은 순. 지연님 원본 k-medoids 해 기준
NAMES_12 = {
    'N1': {'name': '집밥 규칙형', 'summary': '외식이 적고 세 끼를 규칙적으로 챙기는 편이에요.',
           'claims': [('eating_out', -1), ('meal_score', +1)]},
    'N2': {'name': '끼니 거르는 형', 'summary': '운동은 적고 끼니를 자주 거르는 편이에요.',
           'claims': [('meal_score', -1), ('aerobic', -1)]},
    'N3': {'name': '규칙식사 저활동형', 'summary': '끼니는 잘 챙기지만 몸을 움직이는 시간이 적은 편이에요.',
           'claims': [('meal_score', +1), ('aerobic', -1)]},
    'A1': {'name': '유산소 활동형', 'summary': '걷기 같은 유산소 활동을 꾸준히 하고 앉아 있는 시간이 짧은 편이에요.',
           'claims': [('aerobic', +1), ('sedentary_min', -1)]},
    'A2': {'name': '운동은 열심, 끼니는 불규칙형', 'summary': '운동은 자주 하지만 끼니를 자주 거르는 편이에요.',
           'claims': [('strength_days', +1), ('meal_score', -1)]},
    'A3': {'name': '운동·식사 균형형', 'summary': '근력운동을 자주 하고 끼니도 규칙적인 편이에요.',
           'claims': [('strength_days', +1), ('aerobic', +1), ('meal_score', +1)]},
    'S1': {'name': '스트레스·운동 부족형', 'summary': '스트레스를 많이 느끼고 운동할 틈이 적은 편이에요.',
           'claims': [('stress', +1), ('aerobic', -1), ('strength_days', -1)]},
    'S2': {'name': '스트레스 유산소형', 'summary': '스트레스는 많지만 유산소 활동을 꾸준히 하는 편이에요.',
           'claims': [('stress', +1), ('aerobic', +1)]},
    'S3': {'name': '스트레스 근력운동형', 'summary': '스트레스는 많지만 근력운동을 자주 하는 편이에요.',
           'claims': [('stress', +1), ('strength_days', +1)]},
    'O1': {'name': '외식 잦은 끼니 거름형', 'summary': '앉아 있는 시간이 길고 외식이 잦으며 끼니를 자주 거르는 편이에요.',
           'claims': [('eating_out', +1), ('meal_score', -1)]},
    'O2': {'name': '외식 잦은 규칙식사형', 'summary': '앉아 있는 시간이 길고 외식이 잦지만 끼니는 규칙적인 편이에요.',
           'claims': [('eating_out', +1), ('meal_score', +1)]},
    'O3': {'name': '외식 잦은 근력운동형', 'summary': '앉아 있는 시간이 길고 외식이 잦지만 근력운동을 자주 하는 편이에요.',
           'claims': [('eating_out', +1), ('strength_days', +1)]},
}
# 대분류 이름과 근거 (지연님 원래 이름 그대로, 근거만 확인)
MACRO_12 = {
    'N': {'name': '비활동형', 'claims': [('aerobic', -1), ('strength_days', -1)]},
    'A': {'name': '운동형', 'claims': [('aerobic', +1), ('strength_days', +1)]},
    'S': {'name': '고스트레스형', 'claims': [('stress', +1)]},
    'O': {'name': '좌식·외식형', 'claims': [('sedentary_min', +1), ('eating_out', +1)]},
}
