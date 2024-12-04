import os
import logging

from src.textgrid_parser import TextGridParser
from src.opensmile_features import OpenSmileFeatures
from config import AUDIO_DIR
from src.database import Database

# Labels to exclude during processing
EXCLUDED_LABELS = {"<sil>", "SIL", ".sil", ".noise", ""}

logging.basicConfig(level=logging.DEBUG)


class SpeechImporter:
    def __init__(self, db):
        super().__init__()
        self.db = db  # Use the passed Database instance
        self.parser = TextGridParser()
        self.feature_extractor = OpenSmileFeatures()
        self.audio_dir = AUDIO_DIR  # Ensure audio directory is set

    @staticmethod
    def clean_intervals(intervals):
        """
        Remove intervals with excluded labels.

        Args:
            intervals (list): List of interval dictionaries with 'text' keys.

        Returns:
            list: Cleaned intervals.
        """
        return [interval for interval in intervals if interval["text"].strip() not in EXCLUDED_LABELS]

    @staticmethod
    def aggregate_features(interval_data):
        """
        Compute mean features for the interval.

        Args:
            interval_data (pd.DataFrame): Frame-level data for an interval.

        Returns:
            dict: Mean feature values.
        """
        return {key: round(value, 6) for key, value in interval_data.mean().to_dict().items()}

    def process_single_recording(self, textgrid_path, audio_path=None):
        """
        Parses intervals, cleans labels, extracts features, and stores data in the database.
        """
        file_name = os.path.basename(textgrid_path).replace(".TextGrid", "")

        if not audio_path:
            audio_path = os.path.join(self.audio_dir, file_name + ".wav")

        if self.db.recording_exists(file_name):
            logging.info(f"Recording '{file_name}' already exists in the database. Skipping.")
            return

        try:
            intervals = self.parser.parse_textgrid(textgrid_path)
        except ValueError as e:
            logging.error(f"Skipping '{textgrid_path}': {e}")
            return

        words = self.clean_intervals(intervals.get("words", []))
        phonemes = self.clean_intervals(intervals.get("phonemes", []))

        if not words or not phonemes:
            logging.warning(f"TextGrid '{textgrid_path}' is missing 'words' or 'phonemes' tiers.")
            return

        try:
            features = self.feature_extractor.process_file(audio_path)
            self.insert_data(file_name, features, words, phonemes)
            logging.info(f"Recording '{file_name}' processed.")
        except Exception as e:
            logging.error(f"Error processing audio file '{audio_path}': {e}")

    def insert_data(self, file_name, features, words, phonemes):
        """
        Insert recording, word, and phoneme features into the database.
        """
        # Recording-level data
        recording_duration = max(word["end"] for word in words)
        recording_mean = self.aggregate_features(features)

        # Prepare frame_values as lists
        frame_values = {
            "timestamps": features.index.round(6).tolist(),
            "values": features.round(6).values.tolist(),
            "feature_names": features.columns.tolist()
        }

        recording_doc = {
            "recording_id": file_name,
            "parent_id": None,
            "text": "recording",
            "start": 0.0,
            "end": recording_duration,
            "duration": recording_duration,
            "features": {
                "mean": recording_mean,
                "frame_values": frame_values  # Store frame_values directly
            }
        }
        self.db.insert_data("recordings", [recording_doc])

        # Word-level data
        word_docs = []
        for word in words:
            word_features = features[(features.index >= word["start"]) & (features.index <= word["end"])]
            if not word_features.empty:
                word_doc = {
                    "recording_id": file_name,
                    "parent_id": None,
                    "text": word["text"],
                    "start": word["start"],
                    "end": word["end"],
                    "duration": word["end"] - word["start"],
                    "features": {
                        "mean": self.aggregate_features(word_features)
                        # No frame_values at word level
                    }
                }
                word_docs.append(word_doc)
            else:
                logging.warning(f"No features found for word '{word['text']}' in recording '{file_name}'.")

        self.db.insert_data("words", word_docs)

        # Phoneme-level data
        phoneme_docs = []
        for phoneme in phonemes:
            phoneme_features = features[(features.index >= phoneme["start"]) & (features.index <= phoneme["end"])]
            if not phoneme_features.empty:
                parent_id = next(
                    (word_doc["_id"] for word_doc in word_docs if
                     word_doc["start"] <= phoneme["start"] < word_doc["end"]),
                    None
                )
                phoneme_doc = {
                    "recording_id": file_name,
                    "parent_id": parent_id,
                    "text": phoneme["text"],
                    "start": phoneme["start"],
                    "end": phoneme["end"],
                    "duration": phoneme["end"] - phoneme["start"],
                    "features": {
                        "mean": self.aggregate_features(phoneme_features)
                        # No frame_values at phoneme level
                    }
                }
                phoneme_docs.append(phoneme_doc)
            else:
                logging.warning(f"No features found for phoneme '{phoneme['text']}' in recording '{file_name}'.")

        self.db.insert_data("phonemes", phoneme_docs)

    def import_files(self, files):
        """
        Handles file pairing and processing for a list of files.

        Args:
            files (list): List of file paths selected by the user.

        Returns:
            list: List of base names for which valid pairs were not found.
        """
        file_pairs = {}

        for file_path in files:
            base_name, ext = os.path.splitext(os.path.basename(file_path))
            base_name = base_name.strip()
            ext = ext.lower()

            if base_name not in file_pairs:
                file_pairs[base_name] = {}
            if ext == '.wav':
                file_pairs[base_name]['audio'] = file_path
            elif ext == '.textgrid':
                file_pairs[base_name]['textgrid'] = file_path

        missing_pairs = []
        for base_name, paths in file_pairs.items():
            audio_file = paths.get('audio')
            textgrid_file = paths.get('textgrid')

            if audio_file and textgrid_file:
                self.process_single_recording(textgrid_file, audio_file)
            else:
                missing_pairs.append(base_name)
                if not audio_file:
                    logging.warning(f"Missing audio file for base name '{base_name}'.")
                if not textgrid_file:
                    logging.warning(f"Missing TextGrid file for base name '{base_name}'.")

        if missing_pairs:
            logging.info(f"Total missing pairs: {len(missing_pairs)}")
        else:
            logging.info("All files processed successfully with valid pairs.")

        return missing_pairs

    def close(self):
        """
        Close the database connection.
        """
        self.db.close_connection()
