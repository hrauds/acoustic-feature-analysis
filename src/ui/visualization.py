import os
import numpy as np
import pandas as pd
import seaborn as sns
import math
from PyQt5.QtCore import Qt
from src.normalization import Normalization
from PyQt5.QtWidgets import QMessageBox


class Visualization:
    def __init__(self):
        sns.set(style='ticks', context='notebook')

    def plot_vowel_chart(self, ax, formant_dict):
        speaker_colors = sns.color_palette("husl", len(formant_dict))
        table_data_raw = []
        table_data_normalized = []

        for speaker_idx, (speaker_label, formant_df) in enumerate(formant_dict.items()):
            norm_formant_df = Normalization.z_score_normalization(formant_df.copy(), ['F1', 'F2'])

            sns.scatterplot(
                x='F2', y='F1', data=norm_formant_df,
                color=speaker_colors[speaker_idx],
                alpha=0.7, ax=ax
            )

            for _, row in norm_formant_df.iterrows():
                ax.text(
                    row['F2'] + 0.1, row['F1'], row['Vowel'],
                    horizontalalignment='left', fontsize=12,
                    color='black', fontweight='bold'
                )

            for idx, row in formant_df.iterrows():
                table_data_raw.append([speaker_label, row['F1'], row['F2'], row['Vowel']])

            for idx, row in norm_formant_df.iterrows():
                table_data_normalized.append([speaker_label, row['zsc_F1'], row['zsc_F2'], row['Vowel']])

        ax.invert_xaxis()
        ax.invert_yaxis()
        ax.set_xlabel("F2 (Hz)")
        ax.set_ylabel("F1 (Hz)")
        ax.set_title("Vowel Chart")

        raw_data_df = pd.DataFrame(table_data_raw, columns=['Speaker', 'F1', 'F2', 'Vowel'])
        normalized_data_df = pd.DataFrame(table_data_normalized, columns=['Speaker', 'zsc_F1', 'zsc_F2', 'Vowel'])

        return raw_data_df, normalized_data_df

    def plot_time_series(self, ax, features_dict, selected_files, selected_features):
        colors = ['blue', 'green', 'red', 'purple', 'orange', 'brown', 'pink', 'gray']
        all_table_data = []

        for idx, file_item in enumerate(selected_files):
            speaker_label = os.path.basename(file_item.data(Qt.UserRole))
            features_df = features_dict.get(speaker_label)

            if features_df is None:
                continue

            time_index = features_df.index.get_level_values('start').total_seconds()
            speaker_data = pd.DataFrame({'Time': time_index})

            for feature in selected_features:
                if feature in features_df.columns:
                    ax.plot(time_index, features_df[feature].values,
                            label=f"{speaker_label} - {feature}",
                            color=colors[idx % len(colors)])

                    speaker_data[f'{feature} - {speaker_label}'] = features_df[feature].values

            all_table_data.append(speaker_data)

        ax.set_title("Selected Features Time-Series")
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Feature Value")
        ax.legend()

        if all_table_data:
            combined_data = pd.concat(all_table_data, axis=1)
            combined_data = combined_data.loc[:, ~combined_data.columns.duplicated()]
            return combined_data
        return None

    def plot_histogram(self, ax, features_dict, selected_feature):
        all_values = [features_df[selected_feature].values.flatten()
                      for features_df in features_dict.values()
                      if selected_feature in features_df.columns]

        if not all_values:
            QMessageBox.warning(None, 'Error', "Selected feature not found in the data.")
            return None

        all_values = np.concatenate(all_values)
        num_bins = int(1 + math.log2(len(all_values))) if len(all_values) > 0 else 10
        bins = np.linspace(all_values.min(), all_values.max(), num_bins + 1)

        all_speaker_data = {}
        for speaker_label, features_df in features_dict.items():
            if selected_feature in features_df.columns:
                feature_values = features_df[selected_feature].values.flatten()
                ax.hist(feature_values, bins=bins, alpha=0.5, label=speaker_label)

                hist_values, _ = np.histogram(feature_values, bins=bins)
                all_speaker_data[speaker_label] = hist_values

        ax.set_xlabel(f"{selected_feature}")
        ax.set_ylabel("Frequency")
        ax.set_title(f'{selected_feature} Histogram')
        ax.legend()

        bin_labels = []
        for i in range(len(bins) - 1):
            lower_bound = bins[i]
            upper_bound = bins[i + 1]
            label = f'{lower_bound:.2f} to {upper_bound:.2f}'
            bin_labels.append(label)
        table_data = pd.DataFrame.from_dict(all_speaker_data, orient='index', columns=bin_labels)
        table_data.insert(0, 'Speaker', table_data.index)
        return table_data

    def plot_boxplot(self, ax, features_dict, selected_feature):
        data = []
        labels = []
        boxplot_table_data = []

        for speaker_label, features_df in features_dict.items():
            if selected_feature in features_df.columns:
                feature_values = features_df[selected_feature].dropna().values.flatten()
                if len(feature_values) > 0:
                    data.append(feature_values)
                    labels.append(speaker_label)
                    summary_stats = {
                        'Speaker': speaker_label,
                        'Min': np.min(feature_values),
                        'Q1': np.percentile(feature_values, 25),
                        'Median': np.median(feature_values),
                        'Q3': np.percentile(feature_values, 75),
                        'Max': np.max(feature_values)
                    }
                    boxplot_table_data.append(summary_stats)

        if not data:
            QMessageBox.warning(None, 'Error', "No data available for the selected feature.")
            return None

        ax.boxplot(data, tick_labels=labels, vert=True, patch_artist=True, whis=2.0,
                   boxprops=dict(facecolor='lightblue', color='blue'),
                   medianprops=dict(color='red'))
        ax.set_ylabel(f'{selected_feature}')
        ax.set_xlabel('Speakers')
        ax.set_title(f'{selected_feature} Boxplot')
        ax.grid(True)

        ax.figure.tight_layout(pad=3.0)
        summary_table = pd.DataFrame(boxplot_table_data)
        summary_table = summary_table[['Speaker', 'Min', 'Q1', 'Median', 'Q3', 'Max']]
        return summary_table

    def plot_radar_chart(self, ax, features_dict, selected_features):
        all_speaker_data_normalized = []
        all_speaker_data_original = []
        speaker_labels = []

        for speaker_label, features_df in features_dict.items():
            if all(feature in features_df.columns for feature in selected_features):
                original_features = features_df[selected_features].mean(axis=0)
                all_speaker_data_original.append(original_features)

                normalized_features = Normalization.min_max_normalize(
                    features_df, selected_features
                ).mean(axis=0)
                all_speaker_data_normalized.append(normalized_features)

                speaker_labels.append(speaker_label)

        if not all_speaker_data_normalized:
            QMessageBox.warning(None, 'Error', "No data available for the selected features.")
            return None, None

        radar_df_normalized = pd.DataFrame(
            all_speaker_data_normalized, columns=selected_features, index=speaker_labels
        )
        radar_df_original = pd.DataFrame(
            all_speaker_data_original, columns=selected_features, index=speaker_labels
        )

        radar_df_normalized.insert(0, 'Speaker', speaker_labels)
        radar_df_original.insert(0, 'Speaker', speaker_labels)

        num_vars = len(selected_features)
        angles = [n / float(num_vars) * 2 * math.pi for n in range(num_vars)]
        angles += angles[:1]

        for idx, (index, row) in enumerate(radar_df_normalized.iterrows()):
            values = row.values[1:].flatten().tolist()
            values += values[:1]

            ax.plot(angles, values, label=row['Speaker'], linewidth=2)
            ax.fill(angles, values, alpha=0.25)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(selected_features)
        ax.set_title("Radar Chart")
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1))

        return radar_df_original, radar_df_normalized
