import opensmile
import logging
from pandas import Timedelta

logging.basicConfig(level=logging.DEBUG)


class OpenSmileFeatures:
    def __init__(self):
        self.smile = opensmile.Smile(
            feature_set=opensmile.FeatureSet.eGeMAPSv02,
            feature_level=opensmile.FeatureLevel.LowLevelDescriptors
        )

    def process_file(self, file_path):
        """Extract features for an entire audiofile."""
        return self.smile.process_file(file_path)

    def extract_features_by_interval(self, features, intervals):
        """Extract features for each interval (word or phoneme)."""
        interval_features = []
        feature_start_index = features.index.get_level_values('start')

        for interval in intervals:
            start_time = Timedelta(seconds=interval["start"])
            end_time = Timedelta(seconds=interval["end"])

            mask = (feature_start_index >= start_time) & (feature_start_index < end_time)
            interval_data = features[mask]

            if interval_data.empty:
                logging.warning(f"No features found for interval {start_time} - {end_time}")
                continue

            avg_features = interval_data.mean().to_dict()
            avg_features.update({
                "label": interval["label"],
                "start": interval["start"],
                "end": interval["end"],
                "duration": interval["duration"]
            })
            interval_features.append(avg_features)

        return interval_features
