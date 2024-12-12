import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity


class SimilarityAnalyzer:
    def prepare_feature_matrix(self, features_dict):
        """
        Convert the dictionary of features into a DataFrame.
        """
        rows = []
        for recording_id, features in features_dict.items():
            combined_mean = {}
            for feat in features:
                combined_mean.update(feat.get('mean', {}))

            row = {"recording_id": recording_id}
            row.update(combined_mean)
            rows.append(row)
        df = pd.DataFrame(rows).set_index("recording_id")

        return df

    def analyze_clusters(self, target_recording, df, top_n):
        X_pca_10d, pca_10d, scaler_10d = self.normalize_and_reduce(df, n_components=10)
        if X_pca_10d is None:
            raise ValueError("Not enough features for clustering.")

        labels, centers = self.cluster(X_pca_10d, n_clusters=4)
        if labels is None:
            raise ValueError("Could not cluster. Labels is None.")

        idx_map = {rid: i for i, rid in enumerate(df.index)}
        if target_recording not in idx_map:
            raise ValueError("Target recording not in dataset.")
        target_idx = idx_map[target_recording]

        # Compute cosine similarities in PCA space
        cos_sims = self.compute_pca_cosine_similarities(df, pca_10d, scaler_10d)
        target_cos_sims = cos_sims[target_idx]
        cos_dists = 1 - target_cos_sims

        # Find top N closest by similarity (highest similarity = lowest distance)
        sim_pairs = [(df.index[i], target_cos_sims[i]) for i in range(len(target_cos_sims)) if i != target_idx]
        sim_pairs.sort(key=lambda x: x[1], reverse=True)
        similar_list = sim_pairs[:top_n]

        # First two PCAs for visualization
        X_pca_vis = X_pca_10d[:, :2]

        return X_pca_vis, labels, df.index, target_recording, similar_list, target_cos_sims, cos_dists

    def analyze_scores(self, target_recording, df, top_n, method='cosine'):
        """
        Analyze similarities:
        - 'cosine': Original feature (scaled) cosine similarity.
        - 'pca_cosine_distance': PCA cosine distance from the target.
        """
        if method == 'cosine':
            # Original feature space similarity
            scaler = StandardScaler()
            scaler.fit(df.values)
            X_scaled = scaler.transform(df.values)

            sim_matrix = cosine_similarity(X_scaled)
            idx_map = {rid: i for i, rid in enumerate(df.index)}
            if target_recording not in idx_map:
                raise ValueError("Target recording not in dataset.")

            target_idx = idx_map[target_recording]
            similarities = sim_matrix[target_idx]

            sim_pairs = [(df.index[i], similarities[i]) for i in range(len(similarities)) if i != target_idx]
            sim_pairs.sort(key=lambda x: x[1], reverse=True)
            similar_list = sim_pairs[:top_n]

            return target_recording, similar_list

        elif method == 'pca_cosine_distance':

            X_pca_10d, pca_10d, scaler_10d = self.normalize_and_reduce(df, n_components=10)
            if X_pca_10d is None:
                raise ValueError("Not enough features to compute PCA distance.")

            idx_map = {rid: i for i, rid in enumerate(df.index)}
            if target_recording not in idx_map:
                raise ValueError("Target recording not in dataset.")
            target_idx = idx_map[target_recording]

            # Compute cosine similarities in PCA
            cos_sims = self.compute_pca_cosine_similarities(df, pca_10d, scaler_10d)
            target_cos_sims = cos_sims[target_idx]

            # Convert to cosine distance
            cos_distances = 1 - target_cos_sims
            distance_pairs = [(df.index[i], cos_distances[i]) for i in range(len(cos_distances)) if i != target_idx]
            distance_pairs.sort(key=lambda x: x[1])  # ascending order of distance
            similar_list = distance_pairs[:top_n]

            return target_recording, similar_list

        else:
            raise ValueError("Unknown method specified.")

    def compute_pca_cosine_similarities(self, df, pca, scaler):
        """
        Compute cosine similarity for all recordings.
        """
        X_scaled = scaler.transform(df.values)
        X_pca = pca.transform(X_scaled)
        return cosine_similarity(X_pca)

    def normalize_and_reduce(self, df, n_components=10):
        """
        Scale features and reduce dimensionality with PCA.
        """
        if df.empty or df.shape[1] == 0:
            return None, None, None
        n_components = min(n_components, df.shape[1])
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df.values)
        pca = PCA(n_components=n_components, random_state=42)
        X_pca = pca.fit_transform(X_scaled)
        return X_pca, pca, scaler

    def cluster(self, X_pca, n_clusters=4):
        """
        Cluster data in PCA-transformed space.
        """
        if X_pca is None or X_pca.size == 0:
            return None, None

        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(X_pca)
        return labels, kmeans.cluster_centers_
