import opensmile
import logging
logging.basicConfig(level=logging.DEBUG)


class OpenSmileFeatures:
    def __init__(self):
        self.smile = opensmile.Smile(
            feature_set=opensmile.FeatureSet.eGeMAPSv02,
            feature_level=opensmile.FeatureLevel.LowLevelDescriptors
        )

    def process_file(self, file_path):
        return self.smile.process_file(file_path)

