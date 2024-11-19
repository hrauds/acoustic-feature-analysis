import opensmile
import logging
from pandas import Timedelta
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
            pd.DataFrame: Features extracted for the entire audio.
        """
        return self.smile.process_file(file_path)

    def extract_features_by_interval(self, features, intervals):
        """
        Extract features for each interval (e.g., word or phoneme).

        Args:
            features (pd.DataFrame): Extracted features from the entire file.
            intervals (list[dict]): List of intervals with start, end, and label information.
        Returns:
            list[dict]: List of features averaged for each interval.
        """
        interval_features = []
        feature_start_index = features.index.get_level_values('start')

        for interval in intervals:
            start_time = Timedelta(seconds=interval["start"])
            end_time = Timedelta(seconds=interval["end"])

            mask = (feature_start_index >= start_time) & (feature_start_index < end_time)
            interval_data = features[mask]

            if interval_data.empty:
                logging.warning(f"No features found for interval {interval['text']} "
                                f"({interval['start']} - {interval['end']})")
                continue

            # Compute mean features for the interval
            avg_features = interval_data.mean().to_dict()

            avg_features.update({
                "text": interval["text"],
                "start": interval["start"],
                "end": interval["end"],
                "duration": interval["duration"]
            })
            interval_features.append(avg_features)

        return interval_features
