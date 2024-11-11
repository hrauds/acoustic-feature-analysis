import logging
from textgrid import TextGrid

logging.basicConfig(level=logging.DEBUG)


class TextGridParser:

    def parse_textgrid(self, textgrid_path):
        """Parse TextGrid file to extract word and phoneme intervals."""
        textgrid = TextGrid.fromFile(textgrid_path)
        word_intervals = []
        phoneme_intervals = []

        for tier in textgrid:
            if tier.name == "HMM-words":
                for interval in tier.intervals:
                    word_intervals.append({
                        "label": interval.mark,
                        "start": interval.minTime,
                        "end": interval.maxTime,
                        "duration": interval.maxTime - interval.minTime
                    })
            elif tier.name == "HMM-phonemes":
                for interval in tier.intervals:
                    phoneme_intervals.append({
                        "label": interval.mark,
                        "start": interval.minTime,
                        "end": interval.maxTime,
                        "duration": interval.maxTime - interval.minTime
                    })

        return {"words": word_intervals, "phonemes": phoneme_intervals}
