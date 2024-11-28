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
            self.words_col = self.db['words']
            self.phonemes_col = self.db['phonemes']
            logging.info("Connected to MongoDB database.")
        except errors.ConnectionFailure as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise e

    def insert_recordings(self, recording_data_list):
        """
        Insert multiple recordings into the recordings collection.

        Args:
            recording_data_list (list): A list of recording documents.
        """
        if not recording_data_list or not isinstance(recording_data_list, list):
            raise ValueError("Invalid recording data list.")

        try:
            self.recordings_col.insert_many(recording_data_list, ordered=False)
            logging.info(f"Inserted {len(recording_data_list)} recordings.")
        except errors.BulkWriteError as bwe:
            logging.warning(f"Some recordings were not inserted: {bwe.details}")
        except errors.PyMongoError as e:
            logging.error(f"Failed to insert recordings: {e}")
            raise e

    def insert_words(self, word_data_list):
        """
        Insert multiple words into the words collection.

        Args:
            word_data_list (list): A list of word documents.
        """
        if not word_data_list or not isinstance(word_data_list, list):
            raise ValueError("Invalid word data list.")

        try:
            self.words_col.insert_many(word_data_list, ordered=False)
            logging.info(f"Inserted {len(word_data_list)} words.")
        except errors.BulkWriteError as bwe:
            logging.warning(f"Some words were not inserted: {bwe.details}")
        except errors.PyMongoError as e:
            logging.error(f"Failed to insert words: {e}")
            raise e

    def insert_phonemes(self, phoneme_data_list):
        """
        Insert multiple phonemes into the phonemes collection.

        Args:
            phoneme_data_list (list): A list of phoneme documents.
        """
        if not phoneme_data_list or not isinstance(phoneme_data_list, list):
            raise ValueError("Invalid phoneme data list.")

        try:
            self.phonemes_col.insert_many(phoneme_data_list, ordered=False)
            logging.info(f"Inserted {len(phoneme_data_list)} phonemes.")
        except errors.BulkWriteError as bwe:
            logging.warning(f"Some phonemes were not inserted: {bwe.details}")
        except errors.PyMongoError as e:
            logging.error(f"Failed to insert phonemes: {e}")
            raise e

    def get_recording_by_id(self, recording_id):
        """
        Get recording's metadata by its ID.

        Args:
            recording_id (str): The ID of the recording to fetch.

        Returns:
            dict or None: The recording document if found, else None.
        """
        try:
            recording = self.recordings_col.find_one({"recording_id": recording_id})
            if recording:
                logging.info(f"Fetched recording with ID: {recording_id}")
            else:
                logging.warning(f"Recording with ID '{recording_id}' not found.")
            return recording
        except errors.PyMongoError as e:
            logging.error(f"Failed to fetch recording: {e}")
            raise e

    def recording_exists(self, recording_id):
        """
        Check if a recording with the given ID exists in the collection.
        """
        try:
            exists = self.recordings_col.find_one({"recording_id": recording_id}, {"_id": 1})
            if exists:
                logging.info(f"Recording with ID '{recording_id}' exists.")
                return True
            else:
                logging.info(f"Recording with ID '{recording_id}' does not exist.")
                return False
        except errors.PyMongoError as e:
            logging.error(f"Failed to check existence of recording with ID '{recording_id}': {e}")
            return False

    def get_all_recordings(self):
        """
        Get all recording IDs from the database.

        Returns:
            list: List of all recording IDs.
        """
        try:
            return [
                recording["recording_id"]
                for recording in self.recordings_col.find({}, {"recording_id": 1})
            ]
        except errors.PyMongoError as e:
            logging.error(f"Failed to retrieve recordings: {e}")
            raise

    def get_features_for_recordings(self, recording_ids, analysis_level):
        """
        Get features for the given recording IDs and analysis level.

        Args:
            recording_ids (list): List of recording IDs.
            analysis_level (str): Analysis level ('recording', 'word', 'phoneme').

        Returns:
            dict: Dictionary with recording IDs as keys and feature data as values.
        """
        features = {}
        try:
            if analysis_level == 'recording':
                collection = self.recordings_col
            elif analysis_level == 'word':
                collection = self.words_col
            elif analysis_level == 'phoneme':
                collection = self.phonemes_col
            else:
                logging.error(f"Invalid analysis level: {analysis_level}")
                return features

            # Get features for each recording id
            for recording_id in recording_ids:
                query = {"recording_id": recording_id}
                cursor = collection.find(query)
                features_list = list(cursor)

                if features_list:
                    if analysis_level == 'phoneme':
                        # "mean" and "intervals"
                        formatted_features = [
                            {
                                "text": feature.get("text"),
                                "start": feature.get("start"),
                                "end": feature.get("end"),
                                "mean": feature.get("features", {}).get("mean"),
                                "intervals": feature.get("features", {}).get("intervals"),
                            }
                            for feature in features_list
                        ]
                    else:
                        # only "mean"
                        formatted_features = [
                            {
                                "text": feature.get("text"),
                                "start": feature.get("start"),
                                "end": feature.get("end"),
                                "mean": feature.get("features", {}).get("mean"),
                            }
                            for feature in features_list
                        ]
                    features[recording_id] = formatted_features
                    logging.info(
                        f"Fetched {len(features_list)} features for recording '{recording_id}' at level '{analysis_level}'.")
                else:
                    logging.warning(f"No features found for recording '{recording_id}' at level '{analysis_level}'.")

            return features
        except Exception as e:
            logging.error(f"Error fetching features for recordings {recording_ids} at level {analysis_level}: {e}")
            return {}

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
