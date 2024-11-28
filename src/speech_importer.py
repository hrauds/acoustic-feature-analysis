import os
import glob
import logging
from tqdm import tqdm
from src.textgrid_parser import TextGridParser
from src.opensmile_features import OpenSmileFeatures
from config import TEXTGRID_DIR, AUDIO_DIR
from src.database import Database

# Labels to exclude during processing
EXCLUDED_LABELS = {"<sil>", "SIL", ".sil", ".noise", ""}

logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for detailed logs


class SpeechImporter:
    def __init__(self, textgrid_dir=TEXTGRID_DIR, audio_dir=AUDIO_DIR):
        self.textgrid_dir = textgrid_dir
        self.audio_dir = audio_dir
        self.parser = TextGridParser()
        self.feature_extractor = OpenSmileFeatures()
        self.db = Database()

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
    def slice_features(features, intervals):
        """
        Extract features for specific intervals from the feature DataFrame.

        Args:
            features (pd.DataFrame): Frame-level features for the entire file.
            intervals (list[dict]): List of intervals with start, end, and text.

        Returns:
            list[dict]: List of interval features with 'mean' and frame-level data.
        """
        sliced_features = []

        for interval in intervals:
            start, end, text = interval["start"], interval["end"], interval["text"]

            # Extract data within the interval
            interval_data = features[(features.index >= start) & (features.index < end)]

            if interval_data.empty:
                logging.warning(f"No features found for interval '{text}' ({start:.3f} - {end:.3f})")
                continue

            sliced_features.append({
                "text": text,
                "start": start,
                "end": end,
                "mean": interval_data.mean().to_dict(),  # Mean feature values
                "intervals": interval_data.to_dict(orient="records")  # Frame-level values
            })

        return sliced_features

    def process_single_recording(self, textgrid_path, audio_path=None):
        """
        Parses intervals, cleans labels, extracts features, and stores data in the database.
        """
        file_name = os.path.basename(textgrid_path).replace(".TextGrid", "")

        if not audio_path:
            audio_path = os.path.join(self.audio_dir, file_name + ".wav")

        if self.db.recording_exists(file_name):
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
            self.insert_recording(file_name, features, words)
            word_docs = self.insert_words(file_name, features, words)
            self.insert_phonemes(file_name, features, phonemes, word_docs)
            logging.info(f"Recording '{file_name}' processed.")
        except Exception as e:
            logging.error(f"Error processing audio file '{audio_path}': {e}")

    def insert_recording(self, file_name, features, words):
        """
        Insert recording-level data into the database.
        """
        recording_duration = max(word["end"] for word in words)
        recording_interval = [{"start": 0.0, "end": recording_duration, "text": "recording"}]
        recording_features = self.slice_features(features, recording_interval)

        if not recording_features:
            logging.error(f"No features extracted for recording '{file_name}'. Skipping insertion.")
            return

        recording_doc = {
            "recording_id": file_name,
            "start": 0.0,
            "end": recording_duration,
            "duration": recording_duration,
            "features": {"mean": recording_features[0]["mean"]}
        }

        self.db.insert_recordings([recording_doc])

    def insert_words(self, file_name, features, words):
        """
        Insert word-level data into the database.
        """
        word_features = self.slice_features(features, words)
        word_docs = [
            {
                "recording_id": file_name,
                "text": word["text"],
                "start": word["start"],
                "end": word["end"],
                "duration": word["end"] - word["start"],
                "features": {"mean": word_feature["mean"]}
            }
            for word, word_feature in zip(words, word_features)
        ]
        self.db.insert_words(word_docs)
        return word_docs

    def insert_phonemes(self, file_name, features, phonemes, word_docs):
        """
        Insert phoneme-level data into the database.
        """
        phoneme_features = self.slice_features(features, phonemes)
        phoneme_docs = [
            {
                "recording_id": file_name,
                "word_id": next((word["_id"] for word in word_docs if word["start"] <= phoneme["start"] < word["end"]), None),
                "text": phoneme["text"],
                "start": phoneme["start"],
                "end": phoneme["end"],
                "duration": phoneme["end"] - phoneme["start"],
                "features": {
                    "mean": phoneme_feature["mean"],
                    "intervals": phoneme_feature["intervals"]
                }
            }
            for phoneme, phoneme_feature in zip(phonemes, phoneme_features)
        ]
        self.db.insert_phonemes(phoneme_docs)

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
            base_name = base_name.strip().lower()
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
                logging.info(f"Processing pair: {base_name}")
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
