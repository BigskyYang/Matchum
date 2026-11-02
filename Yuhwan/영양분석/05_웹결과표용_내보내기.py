# %% [markdown]
# # 웹 '유형별 영양소 결과표'(bigskyyang/web/src/data/nutrientProfiles.json) 입력 CSV 만들기
# 팀장님 스크립트 bigskyyang/scripts/build_nutrient_profiles.py --nutrients 에 넣는 파일
# 형식: ID, year + 재준님 Jaejun/config/targets.json 열 이름 14개 (값 0/1 = 실제 부족·과잉 여부, observed)
# 기준: 2025 KDRI (요약표 PDF와 28/28 대조한 common.py 값), 사람마다 본인 성별·연령대 기준
#   - 13개: 섭취량 < EAR(또는 AI) → 1
#   - 나트륨 과잉: 섭취량 > CDRR → 1  (CDRR 19~64세 2,300 / 65~74세 1,900 / 75세 이상 1,800mg, 요약표 xvi쪽)
# 참고: 웹 결과표에는 없지만 우리 분석에 쓰는 비타민D·E(AI)도 뒤에 붙여둠 (스크립트는 모르는 열을 무시함)

# %%
import numpy as np
import pandas as pd
from common import *

# 최종 11개 유형 (2026-11-02 지연님 kmedoids_finally.py, 시드 고정 버전) → common.FINAL_CLUSTER_FILE
CLUSTER_FILE = FINAL_CLUSTER_FILE
LABEL_COL = 'Micro_Cluster'

d = add_status(load_persons(CLUSTER_FILE, LABEL_COL))

TARGET = {   # 우리 영양소 이름 → targets.json 열 이름
    '단백질': 'Protein_below_EAR', '칼슘': 'Calcium_mg_below_EAR', '마그네슘': 'Magnesium_mg_below_EAR',
    '철': 'Iron_mg_below_EAR', '아연': 'Zinc_mg_below_EAR', '인': 'Phosphorus_below_EAR',
    '비타민A': 'VitaminA_below_EAR', '티아민': 'B1_below_EAR', '리보플라빈': 'B2_mg_below_EAR',
    '엽산': 'Folate_ug_below_EAR', '비타민C': 'VitaminC_mg_below_EAR', '식이섬유': 'Fiber_below_AI',
    '칼륨': 'Potassium_below_AI',
}
out = d[['ID', 'year']].copy()
for n, col in TARGET.items():
    out[col] = d[f'below_{n}']

CDRR = dict(zip(AGE_LABELS, [2300, 2300, 2300, 1900, 1800]))     # 남녀 동일
out['Sodium_above_CDRR'] = (d['영양_N_NA'] > d['age_grp'].map(CDRR).astype(float)).astype(int)
out['VitaminD_below_AI'] = d['below_비타민D']                    # 참고용 (웹 스크립트는 무시)
out['VitaminE_below_AI'] = d['below_비타민E']

path = OUT / '개인별_영양소_부족여부.csv'
out.to_csv(path, index=False, encoding='utf-8-sig')

# 점검: 전체 비율 (가중치 없음 = 팀장님 스크립트와 같은 방식 / 가중치 있음 = 국민 대표값)
chk = pd.DataFrame({'비가중': out.drop(columns=['ID', 'year']).mean(),
                    '가중(wt_tot/3)': out.drop(columns=['ID', 'year']).apply(lambda s: np.average(s, weights=d['w']))})
print('저장:', path.name, out.shape)
print((chk * 100).round(1).to_string())
