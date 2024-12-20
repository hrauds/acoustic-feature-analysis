import pandas as pd

class Normalization:

    @staticmethod
    def Lobify(df, formants):
        """
        Applies Lobanov normalization to the formant frequencies.
        """
        for formant in formants:
            if formant not in df.columns:
                raise ValueError(f"Expected formant column '{formant}' not found in DataFrame.")

            mean = df[formant].mean()
            std = df[formant].std(ddof=0)
            if std == 0:
                df[f"zsc_{formant}"] = 0
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

        # Check if required columns exist
        for f in formants:
            if f not in df.columns:
                raise ValueError(f"Column '{f}' is required for normalization but not found.")

        # Apply Lobanov normalization
        df_norm = df.copy()
        df_norm = Normalization.Lobify(df_norm, formants)

        # Return only the normalized columns to prevent duplication
        return df_norm[['zsc_F1', 'zsc_F2']]

    @staticmethod
    def min_max_normalize(df, features):
        """Normalize the selected features to a range of 0-1."""
        # Ensure features exist in df
        for f in features:
            if f not in df.columns:
                raise ValueError(f"Feature '{f}' not found in DataFrame for min-max normalization.")

        return (df[features] - df[features].min()) / (df[features].max() - df[features].min())
