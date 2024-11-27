from pymongo import MongoClient, errors
from config import MONGO_URI
import logging

logging.basicConfig(level=logging.INFO)


class Database:
    def __init__(self):
        """
        Initialize the database connection and define collections.
        """
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client['speech_analysis']
            self.recordings_col = self.db['recordings']
            self.features_col = self.db['features']
            logging.info("Connected to MongoDB database.")
        except errors.ConnectionFailure as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise e

    def insert_recording(self, recording_data):
        """
        Insert metadata about a recording into the recordings collection.

        Args:
            recording_data (dict): Contains file name, speaker label, duration, intervals, word count, phoneme count.
        """
        if not recording_data or not isinstance(recording_data, dict):
            raise ValueError("Invalid recording data.")

        try:
            self.recordings_col.insert_one(recording_data)
            logging.info(f"Inserted recording: {recording_data['_id']}")
        except errors.DuplicateKeyError:
            logging.warning(f"Recording with ID '{recording_data['_id']}' already exists.")
        except errors.PyMongoError as e:
            logging.error(f"Failed to insert recording: {e}")
            raise e

    def insert_feature(self, feature_data):
        """
        Insert a single feature into the features collection.

        Args:
            feature_data (dict): A dictionary containing features for a word or phoneme.
        """
        if not feature_data or not isinstance(feature_data, dict):
            raise ValueError("Invalid feature data. Expected a non-empty dictionary.")

        try:
            self.features_col.insert_one(feature_data)
            logging.info(f"Inserted feature: {feature_data['_id']}")
        except errors.DuplicateKeyError:
            logging.warning(f"Feature with ID '{feature_data['_id']}' already exists.")
        except errors.PyMongoError as e:
            logging.error(f"Failed to insert feature: {e}")
            raise e

    def insert_features(self, feature_data_list):
        """
        Insert multiple features into the features collection.

        Args:
            feature_data_list (list): A list of dictionaries containing features for words or phonemes.
        """
        if not feature_data_list or not isinstance(feature_data_list, list):
            raise ValueError("Invalid feature data list.")

        try:
            self.features_col.insert_many(feature_data_list, ordered=False)
            logging.info(f"Inserted {len(feature_data_list)} features.")
        except errors.BulkWriteError as bwe:
            logging.warning(f"Some features were not inserted due to errors: {bwe.details}")
        except errors.PyMongoError as e:
            logging.error(f"Failed to insert features: {e}")
            raise e

    def get_recording_by_id(self, recording_id):
        """
        Get recording's metadata by its ID.
        Returns:
            dict or None: The recording document if found, else None.
        """
        try:
            recording = self.recordings_col.find_one({"_id": recording_id})
            if recording:
                logging.info(f"Fetched recording with ID: {recording_id}")
            else:
                logging.warning(f"Recording with ID '{recording_id}' not found.")
            return recording
        except errors.PyMongoError as e:
            logging.error(f"Failed to fetch recording: {e}")
            raise e

    def get_all_recordings(self):
        """
        Get all recording IDs from the database.
        """
        try:
            recordings = self.recordings_col.find({}, {"_id": 1})
            recording_ids = [recording['_id'] for recording in recordings]
            logging.info(f"Retrieved {len(recording_ids)} recordings.")
            return recording_ids
        except errors.PyMongoError as e:
            logging.error(f"Failed to retrieve recordings: {e}")
            raise e

    def get_features_for_recordings(self, recording_ids, analysis_level='recording'):
        """
        Get features for the given recording IDs.
        """
        features_dict = {}
        try:
            for recording_id in recording_ids:
                # query based on analysis_level
                query = {"recording_id": recording_id}
                if analysis_level in ['phoneme', 'word']:
                    query["interval_type"] = analysis_level

                # get features matching the query
                features_cursor = self.features_col.find(query)
                features = list(features_cursor)

                if features:
                    features_dict[recording_id] = features
                    logging.info(f"Fetched {len(features)} '{analysis_level}' features for recording '{recording_id}'.")
                else:
                    logging.warning(f"No '{analysis_level}' features found for recording '{recording_id}'.")

            return features_dict

        except errors.PyMongoError as e:
            logging.error(f"Failed to fetch features: {e}")
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
