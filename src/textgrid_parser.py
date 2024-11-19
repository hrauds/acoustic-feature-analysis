from praatio import textgrid


class TextGridParser:
    def parse_textgrid(self, textgrid_path):
        """
        Parse a TextGrid file to extract word and phoneme intervals.
        Args:
            textgrid_path (str)
        Returns:
            dict: Contains 'words' and 'phonemes' lists, which have dicts with keys: 'text', 'start', 'end', 'duration'.
        """
        tg = textgrid.openTextgrid(textgrid_path, includeEmptyIntervals=True)

        word_intervals = []
        phoneme_intervals = []

        if "HMM-words" in tg.tierNames:
            word_tier = tg._tierDict["HMM-words"]
            for entry in word_tier.entries:
                start, end, label = entry
                word_intervals.append({
                    "text": label.strip(),
                    "start": start,
                    "end": end,
                    "duration": end - start
                })

        if "HMM-phonemes" in tg.tierNames:
            phoneme_tier = tg._tierDict["HMM-phonemes"]
            for entry in phoneme_tier.entries:
                start, end, label = entry
                phoneme_intervals.append({
                    "text": label.strip(),
                    "start": start,
                    "end": end,
                    "duration": end - start
                })

        return {"words": word_intervals, "phonemes": phoneme_intervals}
