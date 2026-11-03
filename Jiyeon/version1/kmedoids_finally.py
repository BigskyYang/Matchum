import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.spatial.distance import cdist

# 1. 시드 초기화 버그를 고친 K-Medoids 
def kmedoids_robust(X, k, max_iter=100, random_state=42):
    # 전역 시드 초기화가 아닌, 독립적인 RandomState 객체 사용
    rng = np.random.RandomState(random_state)
    medoid_indices = rng.choice(len(X), k, replace=False)
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
            
            # 루프 내부에서 시드를 초기화하지 않고 rng.choice를 사용하여 정상적으로 샘플링 진행
            if len(cluster_idx) > 2000:
                sample_idx = rng.choice(cluster_idx, 2000, replace=False)
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

# 2. 데이터 로드 및 PCA
df = pd.read_csv('KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv')
features = [col for col in df.columns if col.startswith('ML_')]
X = df[features].values
X_scaled = StandardScaler().fit_transform(X)

pca = PCA(n_components=5, random_state=42)
X_pca = pca.fit_transform(X_scaled)

# 3. 매크로 7대 군집 및 마이크로 군집화
labels_main = kmedoids_robust(X_pca, k=7, random_state=42)
df['Macro_Cluster'] = labels_main
df['Micro_Cluster'] = df['Macro_Cluster'].astype(str)

idx_g0 = df['Macro_Cluster'] == 0
features_g0 = ['ML_strength_days', 'ML_aerobic', 'ML_sleep_hours', 'ML_sedentary_min']
X_g0 = df.loc[idx_g0, features_g0].values
X_g0_scaled = StandardScaler().fit_transform(X_g0)
labels_g0 = kmedoids_robust(X_g0_scaled, k=3, random_state=42)
map_g0 = {0: 'A(유산소형)', 1: 'B(근력운동형)', 2: 'C(비활동형)'}
df.loc[idx_g0, 'Micro_Cluster'] = [f"Group_0_{map_g0[l]}" for l in labels_g0]

idx_g2 = df['Macro_Cluster'] == 2
features_g2 = ['ML_breakfast_freq_ord', 'ML_aerobic', 'ML_sedentary_min', 'ML_eatingout_freq_ord']
X_g2 = df.loc[idx_g2, features_g2].values
X_g2_scaled = StandardScaler().fit_transform(X_g2)
labels_g2 = kmedoids_robust(X_g2_scaled, k=3, random_state=42)
map_g2 = {0: 'A(균형사교형)', 1: 'B(상쇄다이어트형)', 2: 'C(불규칙쾌락형)'}
df.loc[idx_g2, 'Micro_Cluster'] = [f"Group_2_{map_g2[l]}" for l in labels_g2]

macro_names = {
    1: 'Group_1(스트레스_워커홀릭형)',
    3: 'Group_3(헤비사교_음주흡연형)',
    4: 'Group_4(소셜헬스케어형)',
    5: 'Group_5(수면부족좌식형)',
    6: 'Group_6(비사교흡연형)'
}
for g, name in macro_names.items():
    df.loc[df['Macro_Cluster'] == g, 'Micro_Cluster'] = name

# 4. 엑셀 출력
summary_size = df.groupby('Micro_Cluster').size().rename('인원수(명)')
summary_mean = df.groupby('Micro_Cluster')[features].mean().round(2)
summary_df = pd.concat([summary_size, summary_mean], axis=1)

with pd.ExcelWriter('KMedoids_Final_Corrected.xlsx', engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Raw_Data', index=False)
    summary_df.to_excel(writer, sheet_name='Profile_Summary')

print("수정된 군집화가 완료되었습니다!")