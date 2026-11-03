import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA

# 1. 데이터 로드 및 전처리
ml_data = pd.read_csv('KNHANES_2022_2024_ML_CLUSTER_COMPLETECASE.csv')
features = [col for col in ml_data.columns if col.startswith('ML_')]
X = ml_data[features].copy()

X_scaled = StandardScaler().fit_transform(X)

# 2. 최적 군집 수 탐색 (k=2~10)
inertia = []
silhouette_scores = []
k_range = range(2, 11)

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    inertia.append(kmeans.inertia_)
    silhouette_scores.append(silhouette_score(X_scaled, labels))

# 3. 엘보우 및 실루엣 지표 시각화
fig, ax1 = plt.subplots(figsize=(10, 5))
ax1.plot(k_range, inertia, marker='o', color='b', label='Inertia (Elbow)')
ax1.set_xlabel('Number of Clusters (k)')
ax1.set_ylabel('Inertia', color='b')

ax2 = ax1.twinx()
ax2.plot(k_range, silhouette_scores, marker='s', color='r', label='Silhouette Score')
ax2.set_ylabel('Silhouette Score', color='r')
plt.title('Elbow Method and Silhouette Score for Optimal k')
plt.show()

# 4. PCA 차원 축소를 통한 2차원 군집 산점도 (k=4 기준)
kmeans_main = KMeans(n_clusters=4, random_state=42, n_init=10)
main_labels = kmeans_main.fit_predict(X_scaled)

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

plt.figure(figsize=(8, 6))
sns.scatterplot(x=X_pca[:, 0], y=X_pca[:, 1], hue=main_labels, palette='viridis', alpha=0.6)
plt.title('PCA 2D Projection of Main Clusters (k=4)')
plt.xlabel(f'PCA 1 ({pca.explained_variance_ratio_[0]*100:.1f}%)')
plt.ylabel(f'PCA 2 ({pca.explained_variance_ratio_[1]*100:.1f}%)')
plt.show()