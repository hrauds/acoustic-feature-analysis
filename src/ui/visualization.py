import numpy as np
import pandas as pd
import seaborn as sns
import math
from src.normalization import Normalization


class Visualization:
    def __init__(self):
        sns.set(style='ticks', context='notebook')

    def plot_time_series(self, ax, features_dict):
        """
        Plot time-series data from frame_values for multiple recordings and features.

        Args:
            ax: Matplotlib axis object to plot on.
            features_dict (dict): Dictionary containing features and frame values.

        Returns:
            pd.DataFrame: Combined table data for all features across the timeline.
        """
        if not features_dict:
            raise ValueError("No features provided for plotting.")

        # Collect all DataFrames in a list
        data_frames = []

        for recording_id, features in features_dict.items():
            for feature in features:
                feature_names = list(feature.get("mean", {}).keys())
                frame_values = feature.get("frame_values", [])
                unique_text = feature.get("text", "Unknown")

                if not frame_values or not feature_names:
                    continue

                # Extract timestamps and values
                timestamps = [fv[0] for fv in frame_values]
                values = np.array([fv[1] for fv in frame_values])

                if values.size == 0:
                    continue

                # Create a DataFrame for all features of this item
                df = pd.DataFrame(values, columns=feature_names)
                df.insert(0, 'Time', timestamps)
                df['Recording'] = recording_id
                df['Item'] = unique_text
                data_frames.append(df)

        if not data_frames:
            raise ValueError("No valid frame_values found in features_dict.")

        # Concatenate all dataframe
        combined_df = pd.concat(data_frames, ignore_index=True)
        combined_df.set_index('Time', inplace=True)
        combined_df.sort_index(inplace=True)

        # Plot each feature
        grouped = combined_df.groupby(['Recording', 'Item'])
        for (recording_id, item), group in grouped:
            for feature_name in feature_names:
                if feature_name in group.columns:
                    label = f"{recording_id} - {item} - {feature_name}"
                    ax.plot(
                        group.index,
                        group[feature_name],
                        label=label,
                        marker='o',
                        linestyle='-',
                        linewidth=2,
                        alpha=0.8
                    )

        ax.set_title("Time-Series Visualization")
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Feature Value")
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax.grid(True)

        return combined_df.reset_index()

    def plot_histogram(self, ax, features_dict):
        """
        Plot histograms of a selected feature for multiple recordings.
        """
        # Extract all available features from 'mean'
        all_feature_names = set()
        for features_list in features_dict.values():
            for feature in features_list:
                feature_names = list(feature.get("mean", {}).keys())
                all_feature_names.update(feature_names)
        all_feature_names = sorted(all_feature_names)

        if not all_feature_names:
            raise ValueError("No features available for plotting.")

        if len(all_feature_names) != 1:
            raise ValueError("Multiple features found. Please select exactly one feature to visualize.")

        selected_feature = all_feature_names[0]

        # Collect all values for the selected feature
        all_values = []
        for features_list in features_dict.values():
            for feature in features_list:
                feature_names = list(feature.get("mean", {}).keys())
                if selected_feature not in feature_names:
                    continue
                frame_values = feature.get("frame_values", [])
                if not frame_values:
                    continue
                feature_index = feature_names.index(selected_feature)
                # Extract the feature values for the selected feature
                values = [fv[1][feature_index] for fv in frame_values if len(fv[1]) > feature_index]
                all_values.extend(values)

        if not all_values:
            raise ValueError("Selected feature not found in the data.")

        all_values = np.array(all_values)
        num_bins = int(1 + math.log2(len(all_values))) if len(all_values) > 0 else 10
        bins = np.linspace(all_values.min(), all_values.max(), num_bins + 1)

        all_recording_data = {}

        # Plot histograms for each (Recording, Text) pair
        for recording_id, features_list in features_dict.items():
            for feature in features_list:
                feature_names = list(feature.get("mean", {}).keys())
                if selected_feature not in feature_names:
                    continue
                frame_values = feature.get("frame_values", [])
                if not frame_values:
                    continue
                feature_index = feature_names.index(selected_feature)
                values = [fv[1][feature_index] for fv in frame_values if len(fv[1]) > feature_index]
                if not values:
                    continue
                label = f"{recording_id} - {feature.get('text', 'Unknown')}"
                ax.hist(values, bins=bins, alpha=0.5, label=label)
                hist_values, _ = np.histogram(values, bins=bins)
                all_recording_data[label] = hist_values

        ax.set_xlabel(f"{selected_feature}")
        ax.set_ylabel("Frequency")
        ax.set_title(f"{selected_feature} Histogram")
        ax.legend()

        # Create bin labels
        bin_labels = []
        for i in range(len(bins) - 1):
            lower_bound = bins[i]
            upper_bound = bins[i + 1]
            label = f'{lower_bound:.2f} to {upper_bound:.2f}'
            bin_labels.append(label)

        # Create DataFrame from all_recording_data
        table_data = pd.DataFrame.from_dict(all_recording_data, orient='index', columns=bin_labels)
        table_data.insert(0, 'Recording - Text', table_data.index)

        return table_data

    def plot_boxplot(self, ax, features_dict):
        """
        Plot boxplots of a selected feature for multiple items (words or phonemes).
        """
        # Extract all available features from features_dict
        all_feature_names = set()
        for features_list in features_dict.values():
            for feature in features_list:
                feature_names = list(feature.get("mean", {}).keys())
                all_feature_names.update(feature_names)
        all_feature_names = sorted(all_feature_names)

        if len(all_feature_names) == 0:
            raise ValueError("No features available for plotting.")

        if len(all_feature_names) != 1:
            raise ValueError("Multiple features found. Please select exactly one feature to visualize.")

        selected_feature = all_feature_names[0]

        data = []
        labels = []
        boxplot_table_data = []

        # Collect data per item (word or phoneme)
        for recording_id, features_list in features_dict.items():
            for feature in features_list:
                unique_text = feature.get("text", "Unknown")
                feature_names = list(feature.get("mean", {}).keys())
                if selected_feature not in feature_names:
                    continue
                frame_values = feature.get("frame_values", [])
                if not frame_values:
                    continue
                feature_index = feature_names.index(selected_feature)
                values = [fv[1][feature_index] for fv in frame_values if len(fv[1]) > feature_index]

                if values:
                    values = np.array(values)
                    data.append(values)
                    label = f"{recording_id} - {unique_text}"
                    labels.append(label)
                    summary_stats = {
                        'Recording': recording_id,
                        'Item': unique_text,
                        'Min': np.min(values),
                        'Q1': np.percentile(values, 25),
                        'Median': np.median(values),
                        'Q3': np.percentile(values, 75),
                        'Max': np.max(values)
                    }
                    boxplot_table_data.append(summary_stats)

        if not data:
            raise ValueError("No data available for the selected feature.")

        ax.boxplot(data, labels=labels, vert=True, patch_artist=True, whis=2.0,
                   boxprops=dict(facecolor='lightblue', color='blue'),
                   medianprops=dict(color='red'))
        ax.set_ylabel(f'{selected_feature}')
        ax.set_xlabel('Items')
        ax.set_title(f'{selected_feature} Boxplot')
        ax.grid(True)

        ax.tick_params(axis='x', rotation=45)

        summary_table = pd.DataFrame(boxplot_table_data)
        summary_table = summary_table[['Recording', 'Item', 'Min', 'Q1', 'Median', 'Q3', 'Max']]

        return summary_table

    def plot_radar_chart(self, ax, features_dict):
        """
        Plot a radar chart for multiple recordings and selected features.
        Returns:
            tuple: (original_data_df, normalized_data_df) DataFrames with the original and normalized data.
        """
        # Extract all available features from features_dict
        all_feature_names = set()
        for features_list in features_dict.values():
            for feature in features_list:
                feature_names = list(feature.get("mean", {}).keys())
                all_feature_names.update(feature_names)
        selected_features = sorted(all_feature_names)

        if not selected_features:
            raise ValueError("No features available for plotting.")

        all_recording_data_original = []
        all_recording_data_normalized = []
        recording_labels = []

        for recording_id, features_list in features_dict.items():
            for feature in features_list:
                frame_values_list = []
                frame_values = feature.get("frame_values", [])
                if not frame_values:
                    continue
                feature_names = list(feature.get("mean", {}).keys())
                if not all(f in feature_names for f in selected_features):
                    continue
                feature_indices = [feature_names.index(f) for f in selected_features]
                unique_text = feature.get("text", "Unknown")
                # Extract frame values for the selected features
                for fv in frame_values:
                    if len(fv[1]) >= len(feature_indices):
                        values = [fv[1][i] for i in feature_indices]
                        frame_values_list.append(values)
                if frame_values_list:
                    # Convert to DataFrame
                    df = pd.DataFrame(frame_values_list, columns=selected_features)
                    # Normalize the DataFrame
                    normalized_df = Normalization.min_max_normalize(df, selected_features)

                    # Compute mean of original and normalized features
                    original_features_mean = df.mean(axis=0)
                    normalized_features_mean = normalized_df.mean(axis=0)
                    all_recording_data_original.append(original_features_mean)
                    all_recording_data_normalized.append(normalized_features_mean)
                    label = f"{recording_id} - {unique_text}"
                    recording_labels.append(label)

        if not all_recording_data_normalized:
            raise ValueError("No data available for the selected features.")

        # Create DataFrames for original and normalized data
        radar_df_original = pd.DataFrame(all_recording_data_original, columns=selected_features, index=recording_labels)
        radar_df_normalized = pd.DataFrame(all_recording_data_normalized, columns=selected_features,
                                           index=recording_labels)
        radar_df_original.reset_index(inplace=True)
        radar_df_original.rename(columns={'index': 'Recording'}, inplace=True)
        radar_df_normalized.reset_index(inplace=True)
        radar_df_normalized.rename(columns={'index': 'Recording'}, inplace=True)

        num_vars = len(selected_features)
        angles = [n / float(num_vars) * 2 * math.pi for n in range(num_vars)]
        angles += angles[:1]

        for idx, (index, row) in enumerate(radar_df_normalized.iterrows()):
            values = row[selected_features].values.flatten().tolist()
            values += values[:1]

            ax.plot(angles, values, label=row['Recording'], linewidth=2)
            ax.fill(angles, values, alpha=0.25)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(selected_features)

        ax.set_title("Radar Chart")
        ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))

        return radar_df_original, radar_df_normalized

    def is_vowel_phoneme(self, phoneme, vowel_set):
        """
        Check if the given phoneme is a vowel by cleaning it and comparing against a set of vowel phonemes.

        Args:
            phoneme (str): The phoneme to check.
            vowel_set (set): A set of vowel phonemes to match against.

        Returns:
            bool: True if the phoneme matches a vowel in the set, False otherwise.
        """
        allowed_characters = {'i', 'ii', 'e', 'ee', '{', '{{', 'y', 'yy', 'u', 'uu', 'o', 'oo', 'A', 'AA', '2', '22', '7', '77'}

        phoneme_clean = ''.join(c for c in phoneme if c in allowed_characters)

        return phoneme_clean in vowel_set

    def plot_vowel_chart(self, ax, vowel_data):
        """
        Plot a vowel chart using F1 and F2 frequencies for selected vowels.

        Args:
            ax: Matplotlib axis object.
            vowel_data (list): List of vowel data dictionaries.

        Returns:
            tuple: (vowel_df_original, vowel_df_normalized) DataFrames (original and normalized vowel data).
        """
        # Convert to a DataFrame
        vowel_df_original = pd.DataFrame(vowel_data)

        if vowel_df_original.empty:
            raise ValueError("No valid vowel data to plot.")

        # Lobanov normalization
        vowel_df_normalized = Normalization.normalize_vowels(vowel_df_original)

        # Plot normalized data
        scatter = sns.scatterplot(
            x='zsc_F2',
            y='zsc_F1',
            hue='Recording',
            data=vowel_df_normalized,
            ax=ax,
            palette='husl',
            legend='full'
        )

        # Vowel symbols
        for _, row in vowel_df_normalized.iterrows():
            ax.text(
                row['zsc_F2'] + 0.02, row['zsc_F1'], row['Phoneme'],
                horizontalalignment='left', fontsize=10, color='black', fontweight='bold'
            )

        # Invert axes
        ax.invert_xaxis()
        ax.invert_yaxis()

        ax.set_xlabel("Normalized F2 (z-score)")
        ax.set_ylabel("Normalized F1 (z-score)")
        ax.set_title("Vowel Chart (Lobanov Normalization)")
        ax.grid(True)

        # Adjust legend
        ax.legend(title='Recording', loc='upper right', bbox_to_anchor=(1.25, 1.0))

        return vowel_df_original, vowel_df_normalized



