import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.spatial.distance import cdist

# 1. 속도 개선 및 안정화된 K-Medoids 자체 구현 함수
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
            
            # 2000명 이상인 거대 군집은 연산 속도를 위해 샘플링 처리
            if len(cluster_idx) > 2000:
                np.random.seed(random_state)
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

# 2. 데이터 로드 및 전처리
print("데이터를 로드하고 전처리를 진행합니다...")
df = pd.read_csv('KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv')
features = [col for col in df.columns if col.startswith('ML_')]
X = df[features].values
X_scaled = StandardScaler().fit_transform(X)

# 3. 1단계: PCA(주성분 분석) 기반 라이프스타일 7대 대분류
# (단순 튀는 값을 잡는 것을 방지하고 전반적인 패턴을 보기 위함)
print("1단계: 라이프스타일 7대 분류 진행 중...")
pca = PCA(n_components=5, random_state=42)
X_pca = pca.fit_transform(X_scaled)

labels_main = kmedoids_fast(X_pca, k=7, random_state=42)
df['Macro_Cluster'] = labels_main
df['Micro_Cluster'] = df['Macro_Cluster'].astype(str)

# 4. 2단계: 구성원이 가장 많은 그룹 0과 2의 세부 군집화 (Micro Clustering)
print("2단계: 주요 그룹 세부 군집화 진행 중...")

# [그룹 0 분할] 기준: 운동방식 (근력, 유산소, 수면, 좌식시간)
idx_g0 = df['Macro_Cluster'] == 0
features_g0 = ['ML_strength_days', 'ML_aerobic', 'ML_sleep_hours', 'ML_sedentary_min']
X_g0 = df.loc[idx_g0, features_g0].values
X_g0_scaled = StandardScaler().fit_transform(X_g0)
labels_g0 = kmedoids_fast(X_g0_scaled, k=3, random_state=42)
map_g0 = {0: 'A(유산소형)', 1: 'B(근력운동형)', 2: 'C(비활동형)'}
df.loc[idx_g0, 'Micro_Cluster'] = [f"Group_0_{map_g0[l]}" for l in labels_g0]

# [그룹 2 분할] 기준: 아침식사 및 활동성 (아침빈도, 유산소, 외식빈도)
idx_g2 = df['Macro_Cluster'] == 2
features_g2 = ['ML_breakfast_freq_ord', 'ML_aerobic', 'ML_sedentary_min', 'ML_eatingout_freq_ord']
X_g2 = df.loc[idx_g2, features_g2].values
X_g2_scaled = StandardScaler().fit_transform(X_g2)
labels_g2 = kmedoids_fast(X_g2_scaled, k=3, random_state=42)
map_g2 = {0: 'A(균형사교형)', 1: 'B(상쇄다이어트형)', 2: 'C(불규칙쾌락형)'}
df.loc[idx_g2, 'Micro_Cluster'] = [f"Group_2_{map_g2[l]}" for l in labels_g2]

# 분할하지 않은 나머지 그룹 직관적 네이밍
macro_names = {
    1: 'Group_1(스트레스_워커홀릭형)',
    3: 'Group_3(헤비사교_음주흡연형)',
    4: 'Group_4(소셜헬스케어형)',
    5: 'Group_5(수면부족좌식형)',
    6: 'Group_6(비사교흡연형)'
}
for g, name in macro_names.items():
    df.loc[df['Macro_Cluster'] == g, 'Micro_Cluster'] = name

# 5. 요약 통계 테이블 생성
summary_size = df.groupby('Micro_Cluster').size().rename('인원수(명)')
summary_mean = df.groupby('Micro_Cluster')[features].mean().round(2)
summary_df = pd.concat([summary_size, summary_mean], axis=1)

output_file = 'KMedoids_Lifestyle_MicroClustered.xlsx'

# 6. 다중 시트 및 스타일이 적용된 엑셀 파일 저장
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Raw_Data', index=False)
    summary_df.to_excel(writer, sheet_name='Profile_Summary')
    
    # 엑셀 헤더 스타일링 (선택 사항)
    workbook = writer.book
    worksheet = writer.sheets['Profile_Summary']
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    
    header_fill = PatternFill(start_color='2F75B5', end_color='2F75B5', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True)
    thin_border = Border(left=Side(style='thin', color='D9D9D9'),
                         right=Side(style='thin', color='D9D9D9'),
                         top=Side(style='thin', color='D9D9D9'),
                         bottom=Side(style='thin', color='D9D9D9'))
    
    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    for row in worksheet.iter_rows(min_row=1, max_row=worksheet.max_row, min_col=1, max_col=worksheet.max_column):
        for cell in row:
            cell.border = thin_border
            
    worksheet.column_dimensions['A'].width = 25

print(f"모든 과정이 성공적으로 완료되었습니다. 파일명: {output_file}")