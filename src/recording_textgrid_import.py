import os
import glob
import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
from src.textgrid_parser import TextGridParser
from src.opensmile_features import OpenSmileFeatures
from config import TEXTGRID_DIR, AUDIO_DIR
from src.database import Database

# Labels to exclude during processing
EXCLUDED_LABELS = {"<sil>", "SIL", ".sil", ".noise", ""}


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
        Removes intervals with excluded labels.
        Args:
            intervals (list): List of interval dictionaries with 'text' keys.
        Returns:
            list: Cleaned intervals.
        """
        cleaned_intervals = []
        for interval in intervals:
            label = interval["text"].strip()
            if label not in EXCLUDED_LABELS:
                cleaned_intervals.append(interval)
        return cleaned_intervals

    @staticmethod
    def visualize_distributions(text_counts):
        """
        Visualize word and phoneme distributions as bar charts.
        Args:
            text_counts (pd.DataFrame): DataFrame containing label counts by type and text.
        """
        sns.set_theme(style="whitegrid")

        # Word distribution
        word_counts = text_counts[text_counts["type"] == "word"]
        plt.figure(figsize=(16, 8))
        sns.barplot(
            x="text",
            y="count",
            data=word_counts.sort_values(by="count", ascending=False),
            color="blue"
        )
        plt.title("Word Distribution", fontsize=16)
        plt.xlabel("Words", fontsize=14)
        plt.ylabel("Count", fontsize=14)
        plt.xticks(rotation=45, fontsize=12, ha='right')
        plt.tight_layout()
        plt.show()

        # Phoneme distribution
        phoneme_counts = text_counts[text_counts["type"] == "phoneme"]
        plt.figure(figsize=(16, 8))
        sns.barplot(
            x="text",
            y="count",
            data=phoneme_counts.sort_values(by="count", ascending=False),
            color="green"
        )
        plt.title("Phoneme Distribution", fontsize=16)
        plt.xlabel("Phonemes", fontsize=14)
        plt.ylabel("Count", fontsize=14)
        plt.xticks(rotation=45, fontsize=12, ha='right')
        plt.tight_layout()
        plt.show()

    def process_single_recording(self, textgrid_path, audio_path=None):
        """
        Parses intervals, cleans labels, extracts features and stores data in the database.
        """
        file_name = os.path.basename(textgrid_path).replace(".TextGrid", "")
        speaker_label = file_name.split("_")[-1]

        # Check if the recording already exists in the database
        if self.db.recordings_col.find_one({"_id": file_name}):
            logging.info(f"Recording {file_name} already exists in the database.")
            return

        if not audio_path:
            audio_path = os.path.join(self.audio_dir, file_name + ".wav")

        # Parse the TextGrid
        try:
            intervals = self.parser.parse_textgrid(textgrid_path)
        except ValueError as e:
            logging.error(f"Skipping {textgrid_path}: {e}")
            return

        # Clean intervals
        words = self.clean_intervals(intervals["words"])
        phonemes = self.clean_intervals(intervals["phonemes"])

        # Extract audio features
        features = self.feature_extractor.process_file(audio_path)
        word_features = self.feature_extractor.extract_features_by_interval(features, words)
        phoneme_features = self.feature_extractor.extract_features_by_interval(features, phonemes)

        # Insert recording data into the database
        recording_data = {
            "_id": file_name,
            "file_name": os.path.basename(audio_path),
            "speaker_label": speaker_label,
            "duration": features.index.get_level_values('end').max().total_seconds(),
            "intervals": {
                "words": words,
                "phonemes": phonemes,
            },
            "word_count": len(words),
            "phoneme_count": len(phonemes),
        }
        self.db.insert_recording(recording_data)

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

        try:
            self.db.insert_features(feature_records)
        except Exception as e:
            logging.error(f"Error inserting features for recording {file_name}: {e}")

        return words, phonemes

    def process_all_recordings(self):
        """
        Process all TextGrid files in the directory and their audio files.
        Cleans labels, extracts features, stores in the database and visualizes label distributions.
        """
        data = []

        for textgrid_path in tqdm(glob.glob(os.path.join(self.textgrid_dir, '*.TextGrid')),
                                  desc="Processing TextGrids"):
            result = self.process_single_recording(textgrid_path)
            if result:
                words, phonemes = result
                for word in words:
                    data.append({"type": "word", "text": word["text"]})
                for phoneme in phonemes:
                    data.append({"type": "phoneme", "text": phoneme["text"]})

        # Create a DataFrame only if data exists
        if not data:
            logging.info("Already exist in the database.")
            return

        df = pd.DataFrame(data)

        if 'type' not in df.columns or 'text' not in df.columns:
            logging.error("DataFrame does not contain 'type' or 'text' columns.")
            return

        text_counts = df.groupby(['type', 'text']).size().reset_index(name='count')
        self.visualize_distributions(text_counts)

    def close(self):
        """
        Close the database connection.
        """
        self.db.close_connection()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    importer = SpeechImporter()
    importer.process_all_recordings()
    importer.close()
