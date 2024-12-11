import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

class SimilarityAnalyzer:

    def prepare_feature_matrix(self, features_dict):
        rows = []
        for recording_id, features in features_dict.items():

            mean_features = features.get("mean", {})
            if not mean_features:
                continue

            row = {"recording_id": recording_id}
            row.update(mean_features)
            rows.append(row)

        df = pd.DataFrame(rows).set_index("recording_id")
        return df

    def analyze_scores(self, target_recording, df, top_n, method='pca'):
        if method == 'pca':
            # PCA similarity
            # X_pca, pca, scaler = self.normalize_and_reduce(df, n_components=10)
            # if X_pca is None:
            #    raise ValueError("Not enough features")
            # similar_list = self.find_similar_recordings(target_recording, df, pca, scaler, top_n=top_n)
            pass
        else:
            # Feature cosine distance
            scaler = StandardScaler()
            scaler.fit(df.values)
            similar_list = self.find_similar_recordings(target_recording, df, pca=None, scaler=scaler, top_n=top_n)

        if not similar_list:
            raise ValueError("No similar recordings found with the chosen method.")

        return target_recording, similar_list

    def find_similar_recordings(self, target_recording_id, df, pca, scaler, n=5):
        if target_recording_id not in df.index:
            raise ValueError("Target recording not in dataset.")

        if pca is None:
            if scaler is not None:
                X = scaler.transform(df.values)
            else:
                X = df.values
        else:
            X_scaled = scaler.transform(df.values)
            X = pca.transform(X_scaled)

        sim_matrix = cosine_similarity(X)
        idx_map = {rid: i for i, rid in enumerate(df.index)}
        target_idx = idx_map[target_recording_id]

        similarities = sim_matrix[target_idx]
        sim_pairs = [(df.index[i], similarities[i]) for i in range(len(similarities)) if i != target_idx]
        sim_pairs.sort(key=lambda x: x[1], reverse=True)

        return sim_pairs[:n]
