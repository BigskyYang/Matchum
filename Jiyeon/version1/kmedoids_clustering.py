import pandas as pd
import numpy as np
import time
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist

# 1. K-Medoids 자체 구현 함수 (추가 설치 불필요)
def kmedoids_fast(X, k, max_iter=100, random_state=42):
    np.random.seed(random_state)
    medoid_indices = np.random.choice(len(X), k, replace=False)
    medoids = X[medoid_indices]
    
    for _ in range(max_iter):
        distances = cdist(X, medoids, metric='euclidean')
        labels = np.argmin(distances, axis=1)
        
        new_medoid_indices = np.zeros(k, dtype=int)
        for i in range(k):
            cluster_idx = np.where(labels == i)[0]
            if len(cluster_idx) == 0:
                new_medoid_indices[i] = medoid_indices[i]
                continue
            
            # 연산 속도 최적화를 위한 샘플링 처리
            if len(cluster_idx) > 2000:
                np.random.seed(42)
                sample_idx = np.random.choice(cluster_idx, 2000, replace=False)
                cluster_points = X[sample_idx]
            else:
                sample_idx = cluster_idx
                cluster_points = X[sample_idx]
                
            intra_dist = cdist(cluster_points, cluster_points, metric='euclidean')
            best_idx = np.argmin(intra_dist.sum(axis=1))
            new_medoid_indices[i] = sample_idx[best_idx]
            
        if np.array_equal(medoid_indices, new_medoid_indices):
            break
        medoid_indices = new_medoid_indices
        medoids = X[medoid_indices]
        
    return labels

# 2. 데이터 로드 및 1단계 대분류 (k=7)
print("데이터 로드 및 대분류(k=7) 진행 중...")
df = pd.read_csv('KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv')
features = [col for col in df.columns if col.startswith('ML_')]
X = df[features].values
X_scaled = StandardScaler().fit_transform(X)

labels_main = kmedoids_fast(X_scaled, k=7)
df['Main_Cluster_KMedoids'] = labels_main
df['Micro_Cluster'] = df['Main_Cluster_KMedoids'].astype(str)

# 3. 2단계 마이크로 군집화 (그룹 0은 k=4, 그룹 1, 2, 3은 k=3)
print("마이크로 군집화 진행 중 (그룹 0: k=4 / 그룹 1,2,3: k=3)...")

# 그룹 0 (k=4 적용: A, B, C, D)
idx_g0 = df['Main_Cluster_KMedoids'] == 0
X_g0 = df.loc[idx_g0, features].values
X_g0_scaled = StandardScaler().fit_transform(X_g0)
labels_g0 = kmedoids_fast(X_g0_scaled, k=4)
map_g0 = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
df.loc[idx_g0, 'Micro_Cluster'] = [f"Group_0_{map_g0[l]}" for l in labels_g0]

# 그룹 1, 2, 3 (k=3 적용: A, B, C)
for g in [1, 2, 3]:
    idx_g = df['Main_Cluster_KMedoids'] == g
    X_g = df.loc[idx_g, features].values
    X_g_scaled = StandardScaler().fit_transform(X_g)
    labels_g = kmedoids_fast(X_g_scaled, k=3)
    map_g = {0: 'A', 1: 'B', 2: 'C'}
    df.loc[idx_g, 'Micro_Cluster'] = [f"Group_{g}_{map_g[l]}" for l in labels_g]

# 분할하지 않은 나머지 그룹(4, 5, 6)은 기본 이름 유지
for g in [4, 5, 6]:
    df.loc[df['Main_Cluster_KMedoids'] == g, 'Micro_Cluster'] = f"Group_{g}"

# 4. 요약 통계 테이블 생성
summary_size = df.groupby('Micro_Cluster').size().rename('인원수(명)')
summary_mean = df.groupby('Micro_Cluster')[features].mean().round(2)
summary_df = pd.concat([summary_size, summary_mean], axis=1)

# 5. 다중 시트 엑셀 파일 저장
output_file = 'KMedoids_Optimized_MicroClustered.xlsx'
print(f"엑셀 파일 생성 중 ({output_file})...")

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Raw_Data', index=False)
    summary_df.to_excel(writer, sheet_name='Profile_Summary')

print("모든 과정이 성공적으로 완료되었습니다!")