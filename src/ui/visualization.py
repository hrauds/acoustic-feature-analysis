import logging

import numpy as np
import pandas as pd
import math
from src.normalization import Normalization
import plotly.graph_objects as go
import plotly.express as px
from src.similarity_analyzer import SimilarityAnalyzer

class Visualization:
    def __init__(self):
        px.defaults.template = "plotly_white"
        self.default_fontsize = 10
        self.legend_fontsize = 10
        self.title_fontsize = 12
        self.label_fontsize = 10
        self.analyzer = SimilarityAnalyzer()

    def configure_legend(self, fig):
        """
        Configure legend horizontal, positioned at the bottom.
        """
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(
                    size=self.legend_fontsize,
                    color="black"
                ),
                title=dict(
                    text="",
                    font=dict(size=self.legend_fontsize)
                )
            ),
            margin=dict(l=40, r=40, t=60, b=80)  # Bottom margins for legend
        )

    def plot_time_series(self, features_dict):
        """
        Plot time-series data from frame_values for multiple recordings, words, or phonemes.

        Args:
            features_dict (dict): Dictionary containing features and frame values.

        Returns:
            plotly.graph_objects.Figure: Interactive time-series figure.
            pd.DataFrame: Combined table data for all features across the timeline.
        """
        if not features_dict:
            raise ValueError("No features provided for plotting.")

        logging.debug("Starting plot_time_series with features_dict: %s", features_dict)

        # Collect all DataFrames in a list
        data_frames = []

        # Item number counter to handle multiple occurrences
        item_nr = {}

        for recording_id, features in features_dict.items():
            for feature in features:
                feature_names = list(feature.get("mean", {}).keys())
                frame_values = feature.get("frame_values", [])
                unique_text = feature.get("text", "Unknown")

                if not frame_values or not feature_names:
                    continue

                # Assign item number based on (Recording, Item) pair
                key = (recording_id, unique_text)
                item_nr[key] = item_nr.get(key, 0) + 1
                nr = item_nr[key]

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
                df['Nr'] = nr
                data_frames.append(df)

        if not data_frames:
            raise ValueError("No valid frame_values found in features_dict.")

        # Concatenate all dataframes
        combined_df = pd.concat(data_frames, ignore_index=True)
        combined_df['Time'] = pd.to_numeric(combined_df['Time'], errors='coerce')
        combined_df.dropna(subset=['Time'], inplace=True)

        # Sort
        combined_df.sort_values(['Recording', 'Time'], inplace=True)

        # Create unique id for each item
        combined_df['Recording-Item-Nr'] = (
            combined_df['Recording'] + " - " + combined_df['Item'] + " - " + combined_df['Nr'].astype(str)
        )

        melted_df = combined_df.melt(
            id_vars=['Time', 'Recording', 'Item', 'Nr', 'Recording-Item-Nr'],
            var_name='Feature',
            value_name='Value'
        )

        # Unique recordings and features
        unique_recordings = melted_df['Recording'].nunique()
        unique_features = melted_df['Feature'].nunique()
        unique_items = melted_df['Item'].nunique()

        # Determine color column based on the data
        if 'Item' in melted_df.columns and unique_items > 1:
            color_column = 'Item'

        elif unique_recordings > 1 and unique_features == 1:
            color_column = 'Recording'

        elif unique_recordings == 1 and unique_features > 1:
            color_column = 'Feature'

        elif unique_recordings > 1 and unique_features > 1:
            melted_df['Recording-Feature'] = melted_df['Recording'] + " - " + melted_df['Feature']
            color_column = 'Recording-Feature'

        else:
            color_column = 'Feature'

        if color_column not in melted_df.columns:
            raise ValueError(f"Color column '{color_column}' does not exist in the data.")

        # Plot using Plotly Express
        try:
            fig = px.line(
                melted_df,
                x='Time',
                y='Value',
                color=color_column,
                markers=True,
                labels={
                    'Time': 'Time (seconds)',
                    'Value': 'Feature Value',
                    'Recording-Item-Nr': 'Recording - Item - Nr',
                    'Feature': 'Feature',
                    'Recording': 'Recording',
                    'Item': 'Item',
                    'Nr': 'Nr',
                    'Recording-Feature': 'Recording - Feature'
                },
                hover_data={
                    'Recording-Item-Nr': False
                },
            )
        except Exception as e:
            logging.error("Plotly failed to create the figure: %s", e)
            raise ValueError(f"Failed to create the plot: {e}")

        self.configure_legend(fig)

        logging.debug("Successfully created time-series plot.")

        return fig, combined_df.reset_index(drop=True)

    def plot_histogram(self, features_dict):
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

        # Collect all values for the selected feature across all recordings
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
                # Extract feature values ensuring the index is within bounds
                values = [fv[1][feature_index] for fv in frame_values if len(fv[1]) > feature_index]
                all_values.extend(values)

        if not all_values:
            raise ValueError("Selected feature not found in the data.")

        all_values = np.array(all_values)

        # Determine the number of bins using Sturges' formula
        num_bins = int(math.ceil(1 + math.log2(len(all_values)))) if len(all_values) > 0 else 10
        bins = np.linspace(all_values.min(), all_values.max(), num_bins + 1)

        # Create bin labels for clarity
        bin_labels = [f'{bins[i]:.2f} to {bins[i + 1]:.2f}' for i in range(len(bins) - 1)]

        all_recording_data = {}

        # Collect histogram counts per bin per recording
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
                hist_values, _ = np.histogram(values, bins=bins)
                all_recording_data[label] = hist_values

        # Create DataFrame from all_recording_data
        table_data = pd.DataFrame.from_dict(all_recording_data, orient='index', columns=bin_labels)
        table_data.reset_index(inplace=True)
        table_data.rename(columns={'index': 'Recording - Text'}, inplace=True)

        melted_df = table_data.melt(
            id_vars=['Recording - Text'],
            var_name='Bin Range',
            value_name='Frequency'
        )

        # Plot using Plotly Express as a bar chart
        fig = px.bar(
            melted_df,
            x='Bin Range',
            y='Frequency',
            color='Recording - Text',
            barmode='group',
            title=f"{selected_feature} Frequency Distribution",
            labels={
                'Bin Range': f"{selected_feature} Range",
                'Frequency': 'Frequency',
                'Recording - Text': 'Recording - Text'
            },
            hover_data={
                'Recording - Text': True,
                'Frequency': True,
                'Bin Range': True
            }
        )

        fig.update_layout(
            yaxis_title="Frequency",
            xaxis_title=f"{selected_feature} Range",
            title=f"{selected_feature} Frequency Distribution",
        )

        self.configure_legend(fig)

        return fig, table_data

    def plot_boxplot(self, features_dict):
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

        # Collect data per item (word or phoneme)
        plot_data = []
        summary_stats = []

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
                    label = f"{recording_id} - {unique_text}"
                    plot_data.append(pd.DataFrame({
                        'Value': values,
                        'Recording - Item': label
                    }))
                    # Compute summary statistics
                    summary_stats.append({
                        'Recording': recording_id,
                        'Item': unique_text,
                        'Min': np.min(values),
                        'Q1': np.percentile(values, 25),
                        'Median': np.median(values),
                        'Q3': np.percentile(values, 75),
                        'Max': np.max(values)
                    })

        if not plot_data:
            raise ValueError("No data available for the selected feature.")

        plot_df = pd.concat(plot_data, ignore_index=True)

        # Create interactive boxplot using Plotly Express
        fig = px.box(
            plot_df,
            y='Value',
            x='Recording - Item',
            color='Recording - Item',
            labels={
                'Value': selected_feature,
                'Recording - Item': 'Recording - Item'
            },
            points='all'  # Show all points
        )

        self.configure_legend(fig)

        # Create summary table DataFrame
        summary_table = pd.DataFrame(summary_stats)

        return fig, summary_table

    def plot_radar_chart(self, features_dict):
        """
        Plot a radar chart for multiple recordings and selected features.
        Args:
            features_dict (dict): Dictionary containing features and frame values.

        Returns:
            plotly.graph_objects.Figure: Interactive radar chart figure.
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
        radar_df_normalized = pd.DataFrame(all_recording_data_normalized, columns=selected_features, index=recording_labels)
        radar_df_original.reset_index(inplace=True)
        radar_df_original.rename(columns={'index': 'Recording'}, inplace=True)
        radar_df_normalized.reset_index(inplace=True)
        radar_df_normalized.rename(columns={'index': 'Recording'}, inplace=True)

        num_vars = len(selected_features)

        # Calculate angles for radar chart
        angles = [n / float(num_vars) * 360 for n in range(num_vars)]
        angles += angles[:1]

        # Create radar chart using Plotly
        fig = go.Figure()

        for idx, row in radar_df_normalized.iterrows():
            values = row[selected_features].tolist()
            values += values[:1]

            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=selected_features + [selected_features[0]],
                fill='toself',
                name=row['Recording'],
                hoverinfo='name+r+theta'
            ))

        self.configure_legend(fig)

        return fig, (radar_df_original, radar_df_normalized)

    def plot_vowel_chart(self, vowel_data):
        """
        Plot an interactive vowel chart using F1 and F2 frequencies for selected vowels.

        Args:
            vowel_data (list): List of vowel data dictionaries.

        Returns:
            plotly.graph_objects.Figure: Interactive vowel chart figure.
            tuple: (vowel_df_original, vowel_df_normalized) DataFrames with the original and normalized vowel data.
        """
        # Convert to a DataFrame
        vowel_df_original = pd.DataFrame(vowel_data)

        if vowel_df_original.empty:
            raise ValueError("No valid vowel data to plot.")

        # Assign Vowel Nr: the occurrence number of the vowel in the word
        vowel_df_original['Vowel Nr'] = vowel_df_original.groupby(['Recording', 'Word']).cumcount() + 1

        # Create a unique identifier for each vowel occurrence
        vowel_df_original['Recording-Word-Vowel-VowelNr'] = (
            vowel_df_original['Recording'] + " - " +
            vowel_df_original['Word'] + " - " +
            vowel_df_original['Vowel'] + " - " +
            vowel_df_original['Vowel Nr'].astype(str)
        )

        # Lobanov normalization
        vowel_df_normalized = Normalization.normalize_vowels(vowel_df_original)

        # Create interactive scatter plot using Plotly Express
        fig = px.scatter(
            vowel_df_normalized,
            x='zsc_F2',
            y='zsc_F1',
            color='Recording-Word-Vowel-VowelNr',
            hover_data={
                'Recording': True,
                'Word': True,
                'Vowel': True,
                'Vowel Nr': True,
                'zsc_F1': True,
                'zsc_F2': True,
                'Recording-Word-Vowel-VowelNr': False
            },
            title="Vowel Chart (Lobanov Normalization)",
            labels={
                'zsc_F2': 'Normalized F2 (z-score)',
                'zsc_F1': 'Normalized F1 (z-score)',
                'Recording-Word-Vowel-VowelNr': 'Recording - Word - Vowel - Vowel Nr'
            },
            text='Vowel'
        )

        fig.update_traces(textposition='top center', textfont=dict(size=10))

        # Switch axes
        fig.update_xaxes(autorange="reversed")
        fig.update_yaxes(autorange="reversed")

        self.configure_legend(fig)

        return fig, (vowel_df_original, vowel_df_normalized)

    def plot_similarity_bars(self, target_recording, measure_pairs, measure_name="Cosine Similarity"):
        """
        """
        if not measure_pairs:
            raise ValueError("No recordings found for plotting.")
        df_measures = pd.DataFrame(measure_pairs, columns=["Recording_ID", measure_name])
        fig = px.bar(df_measures, x="Recording_ID", y=measure_name,
                     title=f"Top Similar to {target_recording} by {measure_name}")
        return fig, df_measures

        return fig, df_measures

    def plot_clusters_with_distances(self, X_pca, labels, recording_ids, target_recording, top_closest_list, cos_sims,
                                     cos_dists):
        """
        Plot clusters and show top similar points.
        Show both cosine similarity and cosine distance in tooltips.
        """
        df_plot = pd.DataFrame(X_pca, columns=["PC1", "PC2"])
        df_plot["recording_id"] = recording_ids
        df_plot["cluster"] = labels.astype(str)
        df_plot["highlight"] = "None"
        df_plot["cosine_similarity"] = cos_sims
        df_plot["cosine_distance"] = cos_dists

        if target_recording in df_plot["recording_id"].values:
            df_plot.loc[df_plot["recording_id"] == target_recording, "highlight"] = "Target"

        closest_ids = [r for r, _ in top_closest_list]
        df_plot.loc[df_plot["recording_id"].isin(closest_ids), "highlight"] = "Closest"

        fig = px.scatter(
            df_plot, x="PC1", y="PC2", color="cluster",
            hover_data=["recording_id", "cosine_similarity", "cosine_distance"],
            symbol="highlight",
            symbol_map={"None": "circle", "Target": "star", "Closest": "diamond"},
            title="Clusters with Closest Recordings Highlighted (PCA Cosine Measures)"
        )
        fig.update_traces(marker=dict(size=10), selector=dict(mode="markers", legendgroup="Target"))
        return fig, df_plot

