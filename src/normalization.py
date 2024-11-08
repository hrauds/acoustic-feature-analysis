class Normalization:
    @staticmethod
    def z_score_normalization(df, formants):
        for formant in formants:
            df[f"zsc_{formant}"] = (df[formant] - df[formant].mean()) / df[formant].std()
        return df

    @staticmethod
    def min_max_normalize(df, features):
        """Normalize the selected features to a range of 0-1."""
        return (df[features] - df[features].min()) / (df[features].max() - df[features].min())
