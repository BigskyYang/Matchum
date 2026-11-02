# %% [markdown]
# # 예측 모델 누수 확인용 재현 실험
# 질문: 같은 날 24시간 회상에서 나온 식품군 정보를 입력에 넣으면 AUC가 얼마나 오르나?
# - 정답: 사람별 KDRI EAR 미만 여부 (N_* 섭취량 = 24시간 회상)
# - 입력 A (설문으로 받을 수 있는 것만): 성별·연령대·생활습관 군집(11개) + 과일(LS_FRUIT)·채소(LS_VEG2) 빈도
# - 입력 B = A + 같은 날 식품군 섭취량 g (보조_MEAT_G, FISH_G, EGG_G, LEGUME_G, DAIRY_G, log1p)
#   → 재준님 모델의 HEI_PROTF·HEI_DAIRY도 같은 24시간 회상(HN_24RC)으로 계산됨 (이용지침서 p250)
# - 로지스틱 회귀, 5-fold 교차검증 AUC
# 한계: HEI 점수 대신 g 사용, 모델도 HistGradientBoosting이 아니라 로지스틱 → 완전히 같은 실험은 아님

# %%
import warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from common import *

warnings.filterwarnings('ignore')
d = add_status(load_persons(ROOT / 'KMedoids_Lifestyle_MicroClustered.xlsx', 'Micro_Cluster'))
LS = ['식습관_LS_FRUIT', '식습관_LS_VEG2']
e = d[d[LS].ne(99).all(axis=1)].copy()          # 99 = 모름/무응답만 제외
A = pd.concat([pd.get_dummies(e[['sex', 'age_grp', 'cluster']].astype(str), drop_first=True).astype(float),
               pd.get_dummies(e[LS].astype(int).astype(str), drop_first=True).astype(float)], axis=1)
SAME_DAY = np.log1p(e[['보조_MEAT_G', '보조_FISH_G', '보조_EGG_G', '보조_LEGUME_G', '보조_DAIRY_G']])

rows = []
for n in ['인', '단백질', '철', '아연', '리보플라빈', '칼슘', '비타민C']:
    y = e[f'below_{n}']
    a = cross_val_score(LogisticRegression(max_iter=3000), A, y, cv=5, scoring='roc_auc').mean()
    b = cross_val_score(LogisticRegression(max_iter=3000), pd.concat([A, SAME_DAY], axis=1), y, cv=5, scoring='roc_auc').mean()
    rows.append(dict(영양소=n, 설문만=a, 같은날식품군추가=b, 증가=b - a))
res = pd.DataFrame(rows)
res.to_csv(OUT / '누수_재현.csv', index=False, encoding='utf-8-sig')
print('사용 인원', len(e))
print(res.round(3).to_string(index=False))
