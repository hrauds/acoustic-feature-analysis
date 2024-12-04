# src/database.py
import json
import os
import pickle
import logging
from config import MONGO_URI, USE_MONGO_MOCK

logging.basicConfig(level=logging.INFO)

if USE_MONGO_MOCK:
    import mongomock
else:
    from pymongo import MongoClient, errors

class Database:
    def __init__(self):
        """
        Initialize the database connection and define collections.
        """
        try:
            if USE_MONGO_MOCK:
                self.client = mongomock.MongoClient()
                logging.info("Using mongomock for MongoDB.")
            else:
                self.client = MongoClient(MONGO_URI)
                logging.info("Connected to MongoDB database.")

            self.db = self.client['speech_analysis']
            self.recordings_col = self.db['recordings']
            self.words_col = self.db['words']
            self.phonemes_col = self.db['phonemes']
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")
            raise e

    def initialize_sample_data(self):
        """
        Initialize the mock database with sample data.
        """
        collection_files = {
            'recordings': 'speech_analysis.recordings.json',
            'words': 'speech_analysis.words.json',
            'phonemes': 'speech_analysis.phonemes.json'
        }

        for collection_name, filename in collection_files.items():
            filepath = os.path.join('data', filename)
            if not os.path.exists(filepath):
                logging.warning(f"Sample data file not found at {filepath}")
                continue

            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    collection = getattr(self, f"{collection_name}_col")
                    collection.insert_many(data)
                    logging.info(f"Initialized '{collection_name}' collection with sample data from {filename}.")
            except Exception as e:
                logging.error(f"Failed to initialize sample data for '{collection_name}': {e}")


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
            return bool(exists)
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
            if analysis_level not in ['recording', 'word', 'phoneme']:
                logging.error(f"Invalid analysis level: {analysis_level}")
                return features

            collection = {
                'recording': self.recordings_col,
                'word': self.words_col,
                'phoneme': self.phonemes_col
            }.get(analysis_level)

            for recording_id in recording_ids:
                query = {"recording_id": recording_id}
                cursor = collection.find(query)
                features_list = list(cursor)

                if features_list:
                    formatted_features = []

                    # Get serialized frame data from the recordings collection
                    recording_doc = self.recordings_col.find_one({"recording_id": recording_id})
                    if not recording_doc:
                        logging.warning(f"Recording data not found for ID '{recording_id}'")
                        continue

                    # full_frame_values = self.deserialize_frame_values(recording_doc["features"]["frame_values"])
                    full_frame_values = recording_doc["features"]["frame_values"]


                    for feature in features_list:
                        start, end = feature.get("start"), feature.get("end")

                        # Slice frame values based on the interval
                        sliced_frame_values = [
                            (float(timestamp), [float(value) for value in values])
                            for timestamp, values in zip(full_frame_values["timestamps"], full_frame_values["values"])
                            if start <= timestamp <= end
                        ]

                        # Downsample frame values for recording and word levels
                        if analysis_level in ['recording', 'word']:
                            if analysis_level == 'recording':
                                step = 10
                            else:
                                step = 2
                            sliced_frame_values = sliced_frame_values[::step]

                        formatted_features.append({
                            "_id": str(feature.get("_id")),
                            "text": feature.get("text"),
                            "start": start,
                            "end": end,
                            "mean": {
                                key: float(value) for key, value in feature.get("features", {}).get("mean", {}).items()
                            },
                            "frame_values": sliced_frame_values
                        })

                    features[recording_id] = formatted_features
                    logging.info(
                        f"Fetched {len(formatted_features)} features for recording '{recording_id}' at level '{analysis_level}'.")
                else:
                    logging.warning(f"No features found for recording '{recording_id}' at level '{analysis_level}'.")

            return features
        except Exception as e:
            logging.error(f"Error fetching features for recordings {recording_ids} at level {analysis_level}: {e}")
            return {}

    @staticmethod
    def deserialize_frame_values(frame_values):
        """
        Deserialize the frame values stored in the database.

        Args:
            frame_values (bytes): Serialized frame values.

        Returns:
            dict: Deserialized frame values with timestamps and feature values.
        """
        try:
            return pickle.loads(frame_values)
        except Exception as e:
            logging.error(f"Failed to deserialize frame values: {e}")
            return None

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
