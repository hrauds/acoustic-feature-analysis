import os
import logging
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
    def aggregate_features(interval_data, level):
        """
        Aggregate features by analysis level.

        Args:
            interval_data (pd.DataFrame): Frame-level data for an interval.
            level (str): Analysis level ('phoneme', 'word', 'recording').

        Returns:
            pd.DataFrame or list[dict]: Down sampled frame data.
        """
        if level == 'phoneme':
            # Keep all
            return interval_data
        elif level == 'word':
            # Keep one per 50 ms
            return interval_data.iloc[::5]
        elif level == 'recording':
            # Keep one per 200 ms
            return interval_data.iloc[::20]

    def slice_features(self, features, intervals, level):
        """
        Extract and aggregate features for specific intervals.

        Args:
            features (pd.DataFrame): Frame-level features for the entire file.
            intervals (list[dict]): List of intervals with start, end, and text.
            level (str): Analysis level ('phoneme', 'word', 'recording').

        Returns:
            list[dict]: List of interval features with frame-level data.
        """
        sliced_features = []

        for interval in intervals:
            start, end, text = interval["start"], interval["end"], interval["text"]

            # Extract data for the interval
            interval_data = features[(features.index >= start) & (features.index <= end)]
            if interval_data.empty:
                logging.warning(f"No features found for interval '{text}' ({start:.3f} - {end:.3f})")
                continue

            # Aggregate features by analysis level
            aggregated_data = self.aggregate_features(interval_data, level)
            aggregated_data = aggregated_data.round(6).astype(float)

            # Include timestamp in each frame
            frame_values = aggregated_data.reset_index().round(6).astype(float).to_dict(orient='records')

            # Compute mean values
            mean_values = {key: round(value, 6) for key, value in interval_data.mean().to_dict().items()}

            sliced_features.append({
                "text": text,
                "start": round(float(start), 6),
                "end": round(float(end), 6),
                "mean": mean_values,
                "frame_values": frame_values
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
            self.insert_data(file_name, features, words, phonemes)
            logging.info(f"Recording '{file_name}' processed.")
        except Exception as e:
            logging.error(f"Error processing audio file '{audio_path}': {e}")

    def insert_data(self, file_name, features, words, phonemes):
        """
        Insert recording, word and phoneme features into the database.
        """
        # Recording-level data
        recording_duration = max(word["end"] for word in words)
        recording_interval = [{"start": 0.0, "end": recording_duration, "text": "recording"}]
        recording_features = self.slice_features(features, recording_interval, level="recording")
        recording_docs = [
            {
                "recording_id": file_name,
                "parent_id": None,
                "text": "recording",
                "start": 0.0,
                "end": recording_duration,
                "duration": recording_duration,
                "features": {
                    "mean": recording_features[0]["mean"],
                    "frame_values": recording_features[0]["frame_values"]
                }
            }
        ]
        self.db.insert_data("recordings", recording_docs)

        word_features = self.slice_features(features, words, level="word")
        word_docs = [
            {
                "recording_id": file_name,
                "parent_id": None,
                "text": word_feature["text"],
                "start": word_feature["start"],
                "end": word_feature["end"],
                "duration": word_feature["end"] - word_feature["start"],
                "features": {
                    "mean": word_feature["mean"],
                    "frame_values": word_feature["frame_values"]
                }
            }
            for word_feature in word_features
        ]
        self.db.insert_data("words", word_docs)

        phoneme_features = self.slice_features(features, phonemes, level="phoneme")
        phoneme_docs = [
            {
                "recording_id": file_name,
                "parent_id": next(
                    (word_doc["_id"] for word_doc in word_docs if
                     word_doc["start"] <= phoneme_feature["start"] < word_doc["end"]),
                    None
                ),
                "text": phoneme_feature["text"],
                "start": phoneme_feature["start"],
                "end": phoneme_feature["end"],
                "duration": phoneme_feature["end"] - phoneme_feature["start"],
                "features": {
                    "mean": phoneme_feature["mean"],
                    "frame_values": phoneme_feature["frame_values"]
                }
            }
            for phoneme_feature in phoneme_features
        ]
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
