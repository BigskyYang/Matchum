import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# 1. 결측치가 없는 데이터 로드 (Complete Case)
ml_data = pd.read_csv('KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv')
features = [col for col in ml_data.columns if col.startswith('ML_')]
X = ml_data[features].copy()

# 스케일링
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 2. [1단계] 전체 4개 대분류
kmeans_main = KMeans(n_clusters=4, random_state=42, n_init=10)
ml_data['Main_Cluster'] = kmeans_main.fit_predict(X_scaled)
ml_data['Sub_Cluster'] = "" # 빈칸 방지를 위한 열 생성

# 3. [2단계] 4개 그룹 각각에 대해 모두 세부 쪼개기 진행
for main_c in range(4):
    # 각 대분류 그룹 인원만 추출
    c_idx = ml_data['Main_Cluster'] == main_c
    c_X = X[c_idx]
    
    # 해당 그룹 인원이 100명 미만이면 2개로, 이상이면 3개로 쪼개기
    n_sub = 3 if len(c_X) >= 100 else 2
    
    # 그룹 내부 스케일링 및 세부 군집화
    c_scaled = StandardScaler().fit_transform(c_X)
    kmeans_sub = KMeans(n_clusters=n_sub, random_state=42, n_init=10)
    sub_labels = kmeans_sub.fit_predict(c_scaled)
    
    # '대분류-소분류' 형태로 텍스트 라벨링 (예: 2-1)
    ml_data.loc[c_idx, 'Sub_Cluster'] = [f"Group_{main_c}-{sub}" for sub in sub_labels]

# 4. 빈칸 없는 최종 결과 파일 저장
ml_data.to_csv('KMeans_All_Subclustered2.csv', index=False)
print("완료: 모든 인원의 세부 유형이 채워진 KMeans_All_Subclustered2.csv 파일이 저장되었습니다.")