from pymongo import MongoClient, errors
from config import MONGO_URI
import logging
logging.basicConfig(level=logging.INFO)


class Database:
    def __init__(self):
        """
        Initialize the database connection and define collections.
        """
        self.client = MongoClient(MONGO_URI)
        self.db = self.client['speech_analysis']
        self.recordings_col = self.db['recordings']
        self.features_col = self.db['features']


    def insert_recording(self, recording_data):
        """
        Insert metadata about a recording into the recordings collection.
        Args:
            recording_data (dict): file name, speaker label, duration, intervals, word count, phoneme count
        """
        if not recording_data or not isinstance(recording_data, dict):
            raise ValueError("Invalid recording data.")

        try:
            self.recordings_col.insert_one(recording_data)

        except errors.PyMongoError as e:
            logging.error(f"Failed to insert recording: {e}")
            raise e

    def insert_feature(self, feature_data):
        """
        Insert a single feature into the features collection.

        Args:
            feature_data (dict): A dictionary containing features for a word or phoneme
        """
        if not feature_data or not isinstance(feature_data, dict):
            raise ValueError("Invalid feature data. Expected a non-empty dictionary.")

        try:
            self.features_col.insert_one(feature_data)
        except errors.PyMongoError as e:
            logging.error(f"Failed to insert feature: {e}")
            raise e

    def insert_features(self, feature_data_list):
        """
        Insert multiple features into the features collection.
        Args:
            feature_data_list (list): A list of dictionaries, contains features for a word or phoneme.
        """
        if not feature_data_list or not isinstance(feature_data_list, list):
            raise ValueError("Invalid feature data list.")

        try:
            self.features_col.insert_many(feature_data_list)
        except errors.PyMongoError as e:
            logging.error(f"Failed to insert features: {e}")
            raise e

    def fetch_recording_by_id(self, recording_id):
        try:
            recording = self.recordings_col.find_one({"_id": recording_id})
            if recording:
                logging.info(f"Fetched recording with ID: {recording_id}")
            else:
                logging.warning(f"Recording with ID {recording_id} not found.")
            return recording
        except errors.PyMongoError as e:
            logging.error(f"Failed to fetch recording: {e}")
            raise e

    def close_connection(self):
        """
        Close the database connection.
        """
        try:
            self.client.close()
            logging.info("Closed MongoDB connection.")
        except errors.PyMongoError as e:
            logging.error(f"Failed to close MongoDB connection: {e}")
            raise e
