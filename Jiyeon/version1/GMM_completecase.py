import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture

# 1. 결측치가 없는 정제된 데이터 로드
print("데이터를 불러오는 중...")
df = pd.read_csv('KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv')

# 2. 'ML_'로 시작하는 14개 생활습관 변수만 추출
features = [col for col in df.columns if col.startswith('ML_')]
X = df[features].copy()

# 3. 데이터 표준화 (StandardScaler)
# 각기 다른 단위(개비, 분, 횟수)를 가진 변수들의 가중치를 공평하게 맞춥니다.
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. GMM (Gaussian Mixture Model) 머신러닝 학습
# K-Means와 달리 '확률'을 기반으로 각 데이터가 어느 그룹에 속할지 부드럽게(Soft) 분류합니다.
print("GMM 모델 학습 및 확률적 군집화 진행 중...")
gmm = GaussianMixture(n_components=4, random_state=42)
df['GMM_Cluster'] = gmm.fit_predict(X_scaled)

# 5. 엑셀 자동 날짜 변환 방지를 위한 텍스트 포맷 적용
df['GMM_Cluster'] = df['GMM_Cluster'].apply(lambda x: f"GMMGroup_{x}")

# 6. 최종 결과 엑셀 파일(.xlsx)로 저장
output_filename = 'GMM_CompleteCase_Result.xlsx'
df.to_excel(output_filename, index=False)

print(f"\n완료! 결과 파일이 저장되었습니다: {output_filename}")
print("\n=== GMM 4개 그룹별 분류 인원 수 ===")
print(df['GMM_Cluster'].value_counts().sort_index())