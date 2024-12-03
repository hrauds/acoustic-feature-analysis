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

        return

    def plot_boxplot(self, ax, features_dict):

        return

    def plot_radar_chart(self, ax, features_dict):
        return

    def plot_vowel_chart(self, ax, filtered_features):
        pass
