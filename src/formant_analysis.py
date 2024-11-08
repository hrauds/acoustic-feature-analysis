import numpy as np
import pandas as pd
import parselmouth


class FormantAnalysis:
    def classify_vowel(self, f1, f2):
        """Simplified vowel classification based on F1 and F2 frequency ranges."""
        if f1 < 400 and f2 > 1500:
            return 'i'
        elif f1 < 400 and f2 < 1500:
            return 'u'
        elif f1 > 600 and 1000 < f2 < 1500:
            return 'a'
        elif f1 < 600 and f2 > 1500:
            return 'e'
        else:
            return 'o'

    def extract_formants(self, file_path, time_step=0.01):
        sound = parselmouth.Sound(file_path)
        formant = sound.to_formant_burg(time_step=time_step)

        f1_list = []
        f2_list = []
        times = []

        for t in np.arange(0, sound.duration, time_step):
            f1 = formant.get_value_at_time(1, t)
            f2 = formant.get_value_at_time(2, t)

            if not np.isnan(f1) and not np.isnan(f2):
                f1_list.append(f1)
                f2_list.append(f2)
                times.append(t)

        vowels = []
        for i in range(len(f1_list)):
            f1 = f1_list[i]
            f2 = f2_list[i]
            vowel = self.classify_vowel(f1, f2)
            vowels.append(vowel)

        formant_df = pd.DataFrame({
            'Time': times,
            'F1': f1_list,
            'F2': f2_list,
            'Vowel': vowels
        })

        return formant_df
