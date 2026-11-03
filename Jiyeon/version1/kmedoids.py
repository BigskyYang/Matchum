import pandas as pd
import numpy as np
import time
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist

# --- [함수] K-Medoids 자체 구현 (추가 설치 불필요) ---
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

# 1. 데이터 로드 및 전처리
print("데이터 로드 및 스케일링 중...")
df = pd.read_csv('KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv')
features = [col for col in df.columns if col.startswith('ML_')]
X = df[features].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 2. 최적의 k=7로 K-Medoids 군집화 실행
print("K-Medoids (k=7) 군집화 진행 중... (데이터 크기에 따라 10~30초 소요)")
start_time = time.time()
kmedoids_labels = kmedoids_fast(X_scaled, k=7)
print(f"군집화 완료! (소요 시간: {time.time() - start_time:.2f}초)")

# 3. 결과 라벨 추가 및 군집별 크기 확인
df['Main_Cluster_KMedoids'] = kmedoids_labels
print("\n[K-Medoids (k=7) 군집별 인원수]")
print(df['Main_Cluster_KMedoids'].value_counts().sort_index())

# 4. 각 군집별 프로파일 평균 요약표 생성
summary_size = df.groupby('Main_Cluster_KMedoids').size().rename('인원수(명)')
summary_mean = df.groupby('Main_Cluster_KMedoids')[features].mean().round(2)
summary_df = pd.concat([summary_size, summary_mean], axis=1)

# 5. 최종 엑셀 파일 저장
output_filename = 'KMedoids_k7_Clustered.xlsx'
print(f"\n엑셀 파일 생성 중... ({output_filename})")

with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Raw_Data', index=False)
    summary_df.to_excel(writer, sheet_name='Cluster_Profile_Summary')

print("완료: 성공적으로 엑셀 파일이 저장되었습니다.")