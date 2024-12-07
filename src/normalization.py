import pandas as pd


class Normalization:

    @staticmethod
    def Lobify(df, formants):
        """
        Applies Lobanov normalization to the formant frequencies.
        """
        for formant in formants:
            mean = df[formant].mean()
            std = df[formant].std(ddof=0)
            if std == 0:
                df[f"zsc_{formant}"] = 0  # Assign zero if standard deviation is zero
            else:
                df[f"zsc_{formant}"] = (df[formant] - mean) / std
        return df

    @staticmethod
    def normalize_vowels(df):
        """
        Normalizes the vowel formants using the Lobanov method.
        Assumes df has columns like 'F1' and 'F2'.
        """
        formants = ['F1', 'F2']
        # Apply Lobanov normalization
        df_norm = df.copy()
        df_norm = Normalization.Lobify(df_norm, formants)

        normalized_columns = [f"zsc_{formant}" for formant in formants]
        df_norm = df_norm[
            normalized_columns + [col for col in df_norm.columns if col not in formants + normalized_columns]]

        return df_norm


    @staticmethod
    def min_max_normalize(df, features):
        """Normalize the selected features to a range of 0-1."""
        return (df[features] - df[features].min()) / (df[features].max() - df[features].min())
