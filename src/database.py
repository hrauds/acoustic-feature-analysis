import json
import os
import logging
import sys
from collections import defaultdict

from bson import ObjectId
from bson.errors import InvalidId
from bson.json_util import loads
from config import MONGO_URI, USE_MONGO_MOCK

logging.basicConfig(level=logging.INFO)

if USE_MONGO_MOCK:
    import mongomock
else:
    from pymongo import MongoClient, errors

class Database:
    def __init__(self):
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
        try:
            base_path = sys._MEIPASS  # PyInstaller temp directory
        except AttributeError:
            base_path = os.path.abspath(".")  # Development environment

        collection_files = {
            'recordings': 'speech_analysis.recordings.json',
            'words': 'speech_analysis.words.json',
            'phonemes': 'speech_analysis.phonemes.json'
        }

        for collection_name, filename in collection_files.items():
            filepath = os.path.join(base_path, 'data', filename)
            if not os.path.exists(filepath):
                logging.warning(f"Sample data file not found at {filepath}")
                continue

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = loads(f.read())
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
                    recording_doc = self.recordings_col.find_one({"recording_id": recording_id})
                    if not recording_doc:
                        logging.warning(f"Recording data not found for ID '{recording_id}'")
                        continue

                    full_frame_values = recording_doc["features"]["frame_values"]

                    for feature in features_list:
                        start, end = feature.get("start"), feature.get("end")

                        # Validate 'start' and 'end'
                        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
                            continue

                        # Slice the main frame_values
                        sliced_frame_values = []
                        for timestamp, values in zip(full_frame_values["timestamps"], full_frame_values["values"]):

                            if not isinstance(timestamp, (int, float)):
                                continue

                            if not isinstance(values, list):
                                continue

                            try:
                                float_timestamp = float(timestamp)
                            except (ValueError, TypeError) as e:
                                logging.error(f"Cannot convert timestamp to float: {timestamp} - {e}")
                                continue

                            try:
                                float_values = [float(value) for value in values]
                            except (ValueError, TypeError) as e:
                                logging.error(f"Cannot convert values to float: {values} - {e}")
                                continue

                            if start <= float_timestamp <= end:
                                sliced_frame_values.append((float_timestamp, float_values))

                        # Downsample for certain levels
                        if analysis_level in ['recording', 'word']:
                            step = 10 if analysis_level == 'recording' else 2
                            sliced_frame_values = sliced_frame_values[::step]

                        word_text = feature.get("word_text", "")

                        # Convert mean features to float
                        mean_features = {}
                        for k, v in feature.get("features", {}).get("mean", {}).items():
                            if isinstance(v, (int, float, str)):
                                try:
                                    mean_features[k] = float(v)
                                except (ValueError, TypeError) as e:
                                    logging.error(f"Cannot convert mean feature '{k}' to float: {v} - {e}")
                            else:
                                logging.error(f"Mean feature '{k}' has invalid type: {type(v)}")

                        formatted_features.append({
                            "_id": str(feature.get("_id")),
                            "text": feature.get("text", ""),
                            "word_text": word_text,
                            "start": start,
                            "end": end,
                            "mean": mean_features,
                            "frame_values": sliced_frame_values
                        })

                    features[recording_id] = formatted_features
                else:
                    logging.warning(f"No features found for recording '{recording_id}' at level '{analysis_level}'.")

            return features
        except Exception as e:
            logging.error(f"Error fetching features for recordings {recording_ids} at level {analysis_level}: {e}")
            return {}

    def get_mean_features(self, recording_ids):
        try:
            collection = self.recordings_col
            query = {"recording_id": {"$in": recording_ids}}
            cursor = collection.find(query)
            features_list = list(cursor)

            grouped_features = defaultdict(list)
            for feature in features_list:
                recording_id = feature.get("recording_id")
                if not recording_id:
                    logging.warning(f"Feature without a recording_id found: {feature}")
                    continue
                mean = feature.get("features", {}).get("mean", {})
                formatted_mean = {key: float(value) for key, value in mean.items() if value is not None}

                formatted_feature = {
                    "_id": str(feature.get("_id")),
                    "text": feature.get("text"),
                    "start": feature.get("start"),
                    "end": feature.get("end"),
                    "mean": formatted_mean
                }
                grouped_features[recording_id].append(formatted_feature)

            features = dict(grouped_features)

            return features

        except Exception as e:
            logging.error(
                f"Error fetching mean features for recordings {recording_ids}")
            return {}



    def get_vowels(self, ids, field):
        """
        Fetches vowel phonemes from the database based on provided IDs and field.

        Parameters:
            ids (list): List of IDs to query.
            field (str): The field to query against (e.g., '_id', 'parent_id', 'recording_id').

        Returns:
            dict: A dictionary mapping IDs to lists of vowel phoneme data.
        """
        allowed_phonemes = {
            'i', 'ii', 'e', 'ee', '{', '{{', 'y', 'yy', 'u',
            'uu', 'o', 'oo', 'a', 'aa', '2', '22', '7', '77'
        }
        allowed_phonemes = {phoneme.lower() for phoneme in allowed_phonemes}

        phoneme_dict = defaultdict(list)

        try:
            if field in ["_id", "parent_id"]:
                converted_ids = []
                for id_str in ids:
                    try:
                        converted_ids.append(ObjectId(id_str))
                    except InvalidId:
                        logging.warning(f"Invalid ObjectId string: {id_str}.")
                ids = converted_ids
                logging.debug(f"Converted string IDs to ObjectId for '{field}' field.")

            # Fields to retrieve
            fields = {
                "_id": 1,
                "text": 1,
                "parent_id": 1,
                "word_text": 1,
                "recording_id": 1,
                "start": 1,
                "end": 1,
                "duration": 1,
                "features.mean.F1frequency_sma3nz": 1,
                "features.mean.F2frequency_sma3nz": 1,
            }

            logging.debug(f"Querying phonemes with {field} in {ids}")
            print(f"Querying phonemes with {field} in {ids}")
            cursor = self.phonemes_col.find({field: {"$in": ids}}, fields)

            # Phoneme validation
            total_phonemes = 0
            for phoneme in cursor:
                total_phonemes += 1
                id_value = phoneme.get(field)

                phoneme_text = phoneme.get("text", "").lower()

                # Check if any allowed phoneme is a substring of phoneme_text
                if not any(allowed_phoneme in phoneme_text for allowed_phoneme in allowed_phonemes):
                    logging.debug(f"Phoneme '{phoneme_text}' not in allowed_phonemes.")
                    continue  # Skip phonemes not allowed

                features = phoneme.get("features", {}).get("mean", {})
                f1 = features.get("F1frequency_sma3nz")
                f2 = features.get("F2frequency_sma3nz")

                phoneme_data = {
                    "Phoneme": phoneme_text,
                    "F1": f1,
                    "F2": f2,
                    "Recording": phoneme.get("recording_id", "Unknown"),
                    "Word": phoneme.get("word_text", "Unknown"),
                    "start": phoneme.get("start"),
                    "end": phoneme.get("end"),
                    "duration": phoneme.get("duration")
                }

                phoneme_dict[id_value].append(phoneme_data)

            return dict(phoneme_dict)

        except errors.PyMongoError as e:
            logging.error(f"PyMongoError during get_vowels: {e}")
            return dict(phoneme_dict)
        except Exception as e:
            logging.error(f"Unexpected error during get_vowels: {e}")
            return dict(phoneme_dict)

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

    def delete_recordings(self, recording_ids):
        """
        Delete all documents with the given recording_ids from the
        'phonemes', 'words', and 'recordings' collections.
        """
        if not isinstance(recording_ids, list):
            raise TypeError("recording_ids must be a list of strings.")

        if not recording_ids:
            logging.warning("No recording_ids provided for deletion.")
            return {"message": "No recording_ids provided for deletion."}

        if not all(isinstance(rid, str) for rid in recording_ids):
            raise ValueError("All recording_ids in the list must be strings.")

        logging.debug(f"Attempting to delete recording_id(s): {recording_ids}")

        query = {"recording_id": {"$in": recording_ids}}

        collections = {
            'phonemes': self.phonemes_col,
            'words': self.words_col,
            'recordings': self.recordings_col
        }

        deletion_results = {}

        for collection_name, collection in collections.items():
            try:
                result = collection.delete_many(query)
                deletion_results[collection_name] = {"deleted_count": result.deleted_count}
                logging.debug(f"Deleted {result.deleted_count} documents from '{collection_name}' collection.")
            except errors.PyMongoError as e:
                logging.error(f"MongoDB error in '{collection_name}' collection: {e}")
                raise RuntimeError(f"Failed to delete from '{collection_name}' collection: {e}") from e

        return deletion_results
