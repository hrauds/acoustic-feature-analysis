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

logging.basicConfig(level=logging.INFO)

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
        cleaned_intervals = [
            interval for interval in intervals
            if interval["text"].strip() not in EXCLUDED_LABELS
        ]
        return cleaned_intervals

    def process_single_recording(self, textgrid_path, audio_path=None):
        """
        Parses intervals, cleans labels, extracts features, and stores data in the database.

        Args:
            textgrid_path (str): Path to the TextGrid file.
            audio_path (str, optional): Path to the audio file. If not provided, it's derived from the TextGrid filename.
        """
        file_name = os.path.basename(textgrid_path).replace(".TextGrid", "")
        speaker_label = file_name.split("_")[-1]

        # Check if the recording already exists in the database
        if self.db.fetch_recording_by_id(file_name):
            logging.info(f"Recording '{file_name}' already exists in the database.")
            return

        if not audio_path:
            audio_path = os.path.join(self.audio_dir, file_name + ".wav")

        # Parse the TextGrid
        try:
            intervals = self.parser.parse_textgrid(textgrid_path)
        except ValueError as e:
            logging.error(f"Skipping '{textgrid_path}': {e}")
            return

        # Clean intervals
        words = self.clean_intervals(intervals.get("words", []))
        phonemes = self.clean_intervals(intervals.get("phonemes", []))

        # Extract audio features
        try:
            features = self.feature_extractor.process_file(audio_path)
            word_features = self.feature_extractor.extract_features_by_interval(features, words)
            phoneme_features = self.feature_extractor.extract_features_by_interval(features, phonemes)
        except Exception as e:
            logging.error(f"Error processing audio file '{audio_path}': {e}")
            return

        # Insert recording data into the database
        try:
            duration = features.index.get_level_values('end').max().total_seconds()
            recording_data = {
                "_id": file_name,
                "file_name": os.path.basename(audio_path),
                "speaker_label": speaker_label,
                "duration": duration,
                "intervals": {
                    "words": words,
                    "phonemes": phonemes,
                },
                "word_count": len(words),
                "phoneme_count": len(phonemes),
            }
            self.db.insert_recording(recording_data)
        except Exception as e:
            logging.error(f"Error inserting recording '{file_name}' into database: {e}")
            return

        # Prepare feature records
        feature_records = []
        for word in word_features:
            feature_records.append({
                "_id": f"{file_name}_word_{word['start']:.3f}",
                "recording_id": file_name,
                "interval_type": "word",
                **word
            })

        for phoneme in phoneme_features:
            feature_records.append({
                "_id": f"{file_name}_phoneme_{phoneme['start']:.3f}",
                "recording_id": file_name,
                "interval_type": "phoneme",
                **phoneme
            })

        # Insert features into the database
        try:
            self.db.insert_features(feature_records)
            logging.info(f"Successfully processed and inserted recording '{file_name}'.")
        except Exception as e:
            logging.error(f"Error inserting features for recording '{file_name}': {e}")

    def import_files(self, files):
        """
        Handles file pairing and processing for a list of files.

        Args:
            files (list): List of file paths selected by the user.

        Returns:
            list: List of base names of files that are missing pairs.
        """
        file_pairs = {}
        for file_path in files:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            ext = os.path.splitext(file_path)[1].lower()
            if base_name not in file_pairs:
                file_pairs[base_name] = {}
            if ext == '.wav':
                file_pairs[base_name]['audio'] = file_path
            elif ext == '.textgrid':
                file_pairs[base_name]['textgrid'] = file_path

        missing_pairs = []
        for base_name, paths in file_pairs.items():
            if 'audio' in paths and 'textgrid' in paths:
                self.process_single_recording(paths['textgrid'], paths['audio'])
            else:
                missing_pairs.append(base_name)
                logging.warning(f"Missing pair for base name '{base_name}'.")

        return missing_pairs

    def process_all_recordings(self):
        """
        Process all TextGrid files in the directory and their corresponding audio files.
        """
        textgrid_paths = glob.glob(os.path.join(self.textgrid_dir, '*.TextGrid'))

        if not textgrid_paths:
            logging.warning("No TextGrid files found in the directory.")
            return

        for textgrid_path in tqdm(textgrid_paths, desc="Processing TextGrids"):
            self.process_single_recording(textgrid_path)

    def close(self):
        """
        Close the database connection.
        """
        self.db.close_connection()
