import opensmile.core.smile
import logging

import pandas as pd

logging.basicConfig(level=logging.INFO)


class OpenSmileFeatures:
    def __init__(self):
        """
        Initialize the OpenSmileFeatures class with the desired feature set and level.
        """
        self.smile = opensmile.Smile(
            feature_set=opensmile.FeatureSet.eGeMAPSv02,
            feature_level=opensmile.FeatureLevel.LowLevelDescriptors
        )

    def process_file(self, file_path):
        """
        Extract features for the entire audio file.

        Args:
            file_path (str): Path to the audio file.

        Returns:
            pd.DataFrame: Features extracted for the entire audio with 'start' as index.
        """
        features = self.smile.process_file(file_path)

        features = features.reset_index(level='start')
        features['start'] = features['start'].dt.total_seconds()

        # Use 'start' as index for slicing
        features.set_index('start', inplace=True)

        # Return sorted DataFrame
        return features.sort_index()
