import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# 1. 결측치가 없는 원본 데이터 로드
print("데이터를 불러오는 중...")
ml_data = pd.read_csv('KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv')
features = [col for col in ml_data.columns if col.startswith('ML_')]
X = ml_data[features].copy()

# 전체 데이터 스케일링
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 2. [1단계] 전체 4개 대분류 (Main_Cluster)
print("1단계: 대분류 군집화 진행 중...")
kmeans_main = KMeans(n_clusters=4, random_state=42, n_init=10)
ml_data['Main_Cluster'] = kmeans_main.fit_predict(X_scaled)
ml_data['Sub_Cluster'] = "" 

# 3. [2단계] 4개 대분류 각각에 대해 세부 쪼개기 진행 (Sub_Cluster)
print("2단계: 세부 군집화 진행 중...")
for main_c in range(4):
    c_idx = ml_data['Main_Cluster'] == main_c
    c_X = X[c_idx]
    
    # 해당 그룹 인원이 100명 미만이면 2개로, 이상이면 3개로 쪼개기
    n_sub = 3 if len(c_X) >= 100 else 2
    
    # 그룹 내부 독립 스케일링 및 세부 군집화
    c_scaled = StandardScaler().fit_transform(c_X)
    kmeans_sub = KMeans(n_clusters=n_sub, random_state=42, n_init=10)
    sub_labels = kmeans_sub.fit_predict(c_scaled)
    
    # '대분류-소분류' 형태로 라벨링
    ml_data.loc[c_idx, 'Sub_Cluster'] = [f"Group_{main_c}-{sub}" for sub in sub_labels]

# 4. [3단계] 타겟 대형 그룹 마이크로 군집화 (Micro_Cluster)
print("3단계: 대형 그룹 마이크로 분할(A/B/C) 진행 중...")
large_clusters = ['Group_1-1', 'Group_3-1', 'Group_3-0', 'Group_1-0']
ml_data['Micro_Cluster'] = ml_data['Sub_Cluster'] # 분할 대상이 아닌 그룹은 기존 라벨 복사

for cluster_name in large_clusters:
    idx = ml_data['Sub_Cluster'] == cluster_name
    X_group = ml_data.loc[idx, features]
    
    # 대형 그룹 내부 독립 스케일링
    X_group_scaled = StandardScaler().fit_transform(X_group)
    
    # 3분할(k=3) 마이크로 군집화
    kmeans_micro = KMeans(n_clusters=3, random_state=42, n_init=10)
    micro_labels = kmeans_micro.fit_predict(X_group_scaled)
    
    # 0, 1, 2 결과를 A, B, C로 변환하여 라벨 업데이트
    label_map = {0: 'A', 1: 'B', 2: 'C'}
    ml_data.loc[idx, 'Micro_Cluster'] = [f"{cluster_name}_{label_map[l]}" for l in micro_labels]

# 5. 최종 결과를 엑셀 파일로 저장 (.xlsx)
output_filename = 'KMeans_Final_MicroClustered.xlsx'
print(f"엑셀 파일 생성 중... ({output_filename})")

# to_csv 대신 to_excel 사용 (engine='openpyxl' 지정)
ml_data.to_excel(output_filename, index=False, engine='openpyxl')

print("완료: 모든 군집화가 적용된 엑셀 파일이 성공적으로 저장되었습니다.")