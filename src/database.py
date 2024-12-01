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

    def insert_data(self, collection_name, data_list):
        """
        Insert documents into a phoneme, word or recording collection.

        Args:
            collection_name (str): Name of the collection ('recordings', 'words', 'phonemes').
            data_list (list): A list of documents to insert.

        Raises:
            ValueError: If the collection name or data list is invalid.
        """
        if not data_list or not isinstance(data_list, list):
            raise ValueError("Invalid data list. Must be a non-empty list.")

        if collection_name == 'recordings':
            collection = self.db['recordings']
        elif collection_name == 'words':
            collection = self.db['words']
        elif collection_name == 'phonemes':
            collection = self.db['phonemes']
        else:
            raise ValueError(f"Invalid collection name: {collection_name}. Must be 'recordings', 'words', or 'phonemes'.")

        try:
            collection.insert_many(data_list, ordered=False)
        except errors.BulkWriteError as bwe:
            logging.warning(f"Some documents were not inserted into '{collection_name}' collection: {bwe.details}")
        except errors.PyMongoError as e:
            logging.error(f"Failed to insert data into '{collection_name}' collection: {e}")

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
                return True
            else:
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
                    formatted_features = [
                        {
                            "text": feature.get("text"),
                            "start": feature.get("start"),
                            "end": feature.get("end"),
                            "mean": feature.get("features", {}).get("mean"),
                            "frame_values": feature.get("features", {}).get("frame_values"),
                        }
                        for feature in features_list
                    ]
                    features[recording_id] = formatted_features
                    logging.info(
                        f"Fetched {len(features_list)} frame values for recording '{recording_id}' at level '{analysis_level}'.")
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
