import os
import glob
import logging
from tqdm import tqdm
from src.textgrid_parser import TextGridParser
from src.opensmile_features import OpenSmileFeatures
from config import TEXTGRID_DIR, AUDIO_DIR
from src.database import Database

logging.basicConfig(level=logging.DEBUG)


def main():
    parser = TextGridParser()
    feature_extractor = OpenSmileFeatures()
    db = Database()

    for textgrid_path in tqdm(glob.glob(os.path.join(TEXTGRID_DIR, '*.TextGrid')), desc="Processing files"):
        file_name = os.path.basename(textgrid_path).replace(".TextGrid", "")
        speaker_label = file_name.split("_")[-1]

        intervals = parser.parse_textgrid(textgrid_path)
        words = intervals["words"]
        phonemes = intervals["phonemes"]

        audio_path = os.path.join(AUDIO_DIR, file_name + ".wav")
        if not os.path.exists(audio_path):
            logging.warning(f"Audio file for {file_name} not found.")
            continue

        features = feature_extractor.process_file(audio_path)

        word_features = feature_extractor.extract_features_by_interval(features, words)
        phoneme_features = feature_extractor.extract_features_by_interval(features, phonemes)

        for word in word_features:
            word.update({"speaker_label": speaker_label, "file_name": file_name + ".wav"})
            db.words_col.insert_one(word)

        for phoneme in phoneme_features:
            phoneme.update({"speaker_label": speaker_label, "file_name": file_name + ".wav"})
            db.phonemes_col.insert_one(phoneme)

        recording_info = {
            "file_name": file_name + ".wav",
            "speaker_label": speaker_label,
            "word_count": len(word_features),
            "phoneme_count": len(phoneme_features),
            "duration": features.index.get_level_values('end').max().total_seconds()
        }
        db.recordings_col.insert_one(recording_info)

    print("Phoneme data ingestion completed.")
    db.client.close()


if __name__ == '__main__':
    main()
