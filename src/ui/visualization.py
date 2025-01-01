import logging
import pandas as pd
import math
from src.normalization import Normalization
import plotly.express as px
from src.similarity_analyzer import SimilarityAnalyzer
import plotly.graph_objects as go
import numpy as np

class Visualization:
    def __init__(self):
        px.defaults.template = "plotly_white"
        self.default_fontsize = 10
        self.legend_fontsize = 10
        self.title_fontsize = 10
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

    def plot_time_series(self, features_dict, analysis_level):
        """
        Plot time-series data from frame_values for multiple recordings, words, or phonemes.
        """
        if not features_dict:
            raise ValueError("No features provided for plotting.")

        logging.debug(f"Starting plot_time_series, analysis_level={analysis_level}")

        data_frames = []

        word_counters = {}
        phoneme_counters = {}

        for recording_id, feature_list in features_dict.items():
            for feat in feature_list:
                frame_values = feat.get("frame_values", [])
                feature_names = list(feat.get("mean", {}).keys())
                if not frame_values or not feature_names:
                    continue

                item_text = feat.get("text", "")
                parent_word = feat.get("word_text", "")
                start_val = feat.get("start", 0.0)
                end_val = feat.get("end", 0.0)

                timestamps = [fv[0] for fv in frame_values]
                matrix = [fv[1] for fv in frame_values]
                if not matrix:
                    continue

                df_vals = pd.DataFrame(matrix, columns=feature_names)
                df_vals.insert(0, 'Timestamp', timestamps)
                df_vals['Recording'] = recording_id

                if analysis_level == 'recording':
                    pass

                elif analysis_level == 'word':
                    df_vals['Word'] = item_text
                    key = recording_id
                    word_counters[key] = word_counters.get(key, 0) + 1
                    df_vals['WordNr'] = word_counters[key]

                elif analysis_level == 'phoneme':
                    df_vals['Word'] = parent_word
                    df_vals['Phoneme'] = item_text
                    key = (recording_id, parent_word)
                    phoneme_counters[key] = phoneme_counters.get(key, 0) + 1
                    df_vals['PhonemeNr'] = phoneme_counters[key]

                df_vals['Start'] = start_val
                df_vals['End'] = end_val

                data_frames.append(df_vals)

        if not data_frames:
            raise ValueError("No valid frame_values found in features_dict.")

        combined_df = pd.concat(data_frames, ignore_index=True)

        combined_df['Timestamp'] = pd.to_numeric(combined_df['Timestamp'], errors='coerce')
        combined_df.dropna(subset=['Timestamp'], inplace=True)
        combined_df.sort_values(['Recording', 'Timestamp'], inplace=True)

        id_vars = ['Timestamp', 'Recording', 'Start', 'End']

        if analysis_level == 'word':
            id_vars.extend(['Word', 'WordNr'])
        elif analysis_level == 'phoneme':
            id_vars.extend(['Word', 'Phoneme', 'PhonemeNr'])

        melted_df = combined_df.melt(
            id_vars=id_vars,
            var_name='Feature',
            value_name='Value'
        )

        def make_label(row):
            if analysis_level == 'recording':
                return f"{row['Recording']}"

            elif analysis_level == 'word':
                return f"{row['Recording']} - {row['Word']} (#{int(row['WordNr'])})"

            elif analysis_level == 'phoneme':
                return (
                    f"{row['Recording']} - {row['Word']} - {row['Phoneme']} (#{int(row['PhonemeNr'])})"
                )

        melted_df['BaseLegendLabel'] = melted_df.apply(make_label, axis=1)

        # If multiple features, append the feature name
        if melted_df['Feature'].nunique() > 1:
            melted_df['Label'] = melted_df['BaseLegendLabel'] + " - " + melted_df['Feature']
        else:
            melted_df['Label'] = melted_df['BaseLegendLabel']

        color_column = 'Label'

        hover_data_cols = ['Feature', 'Recording']

        if analysis_level == 'word':
            hover_data_cols.extend(['Word', 'WordNr'])
        elif analysis_level == 'phoneme':
            hover_data_cols.extend(['Word', 'Phoneme', 'PhonemeNr'])

        # hover_data
        hover_dict = {}
        for col in hover_data_cols:
            if col in melted_df.columns:
                hover_dict[col] = True

        try:
            fig = px.line(
                data_frame=melted_df,
                x='Timestamp',
                y='Value',
                color=color_column,
                markers=True,
                labels={
                    'Timestamp': 'Time (s)',
                    'Value': 'Feature Value',
                    'Feature': 'Acoustic Feature',
                    'Recording': 'Recording ID',
                    'Word': 'Word Text',
                    'WordNr': 'Word #',
                    'Phoneme': 'Phoneme',
                    'PhonemeNr': 'Phoneme #'
                },
                hover_data=hover_dict
            )
        except Exception as e:
            logging.error(f"Plotly failed to create figure: {e}")
            raise ValueError(f"Failed to create the plot: {e}")

        self.configure_legend(fig)

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
            pd.DataFrame: Combined DataFrame with original and normalized data.
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

        # Rename normalized columns to have a _normalized end
        normalized_col_map = {col: f"{col}_normalized" for col in selected_features}
        radar_df_normalized.rename(columns=normalized_col_map, inplace=True)

        # Combine original and normalized data into one DataFrame
        radar_df_combined = pd.merge(radar_df_original, radar_df_normalized, on='Recording')

        # Transpose the table so features are rows and recordings are columns
        radar_df_combined_transposed = radar_df_combined.set_index('Recording').transpose().reset_index()
        radar_df_combined_transposed.rename(columns={'index': 'Feature'}, inplace=True)

        # Sort features: for each selected feature, include the normalized version if it exists
        sorted_features = []
        features_in_data = radar_df_combined_transposed['Feature'].tolist()

        for feature in selected_features:
            sorted_features.append(feature)
            normalized_feature = f"{feature}_normalized"
            if normalized_feature in features_in_data:
                sorted_features.append(normalized_feature)

        # Ensure that all sorted_features exist in the data to avoid KeyError
        sorted_features = [feat for feat in sorted_features if feat in features_in_data]

        # Reorder the DataFrame based on sorted_features
        radar_df_combined_transposed = radar_df_combined_transposed.set_index('Feature').loc[
            sorted_features].reset_index()

        fig = go.Figure()

        for idx, row in radar_df_normalized.iterrows():
            # Extract normalized values in the order of selected_features
            values = [row[f"{feature}_normalized"] for feature in selected_features]
            values += values[:1]

            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=selected_features + [selected_features[0]],
                fill='toself',
                name=row['Recording'],
                hoverinfo='name+r+theta'
            ))

        self.configure_legend(fig)

        return fig, radar_df_combined_transposed

    def plot_vowel_chart(self, vowel_data):
        """
        Plot an interactive vowel chart using F1 and F2 frequencies for selected vowels.

        Args:
            vowel_data (list): List of vowel data dictionaries.

        Returns:
            plotly.graph_objects.Figure: Interactive vowel chart figure.
            pd.DataFrame: Combined DataFrame with original and normalized vowel data.
        """
        if not vowel_data:
            raise ValueError("No vowel data provided.")

        vowel_df_original = pd.DataFrame(vowel_data)
        required_columns = {'Recording', 'Word', 'Vowel', 'F1', 'F2'}
        if vowel_df_original.empty or not required_columns.issubset(vowel_df_original.columns):
            missing = required_columns.difference(vowel_df_original.columns)
            raise ValueError(f"Vowel data is incomplete or missing required columns: {missing}")

        logging.debug("Original Vowel DataFrame:\n%s", vowel_df_original.head())

        try:
            # Assign Vowel Nr and unique identifier
            vowel_df_original['Vowel Nr'] = vowel_df_original.groupby(['Recording', 'Word']).cumcount() + 1
            vowel_df_original['Recording-Word-Vowel-VowelNr'] = (
                    vowel_df_original['Recording'] + " - " +
                    vowel_df_original['Word'] + " - " +
                    vowel_df_original['Vowel'] + " - " +
                    vowel_df_original['Vowel Nr'].astype(str)
            )

            logging.debug("Vowel DataFrame with Identifiers:\n%s", vowel_df_original.head())

            # Normalize vowel data
            normalized_vowel_df = Normalization.normalize_vowels(vowel_df_original)
            logging.debug("Normalized Vowel DataFrame:\n%s", normalized_vowel_df.head())

            if normalized_vowel_df.empty:
                raise ValueError("Normalization produced no data.")

            # Assign the normalized columns
            vowel_df_original['zsc_F1'] = normalized_vowel_df['zsc_F1']
            vowel_df_original['zsc_F2'] = normalized_vowel_df['zsc_F2']

            logging.debug("Vowel DataFrame with Normalized Columns:\n%s", vowel_df_original.head())

            # Create scatter plot
            fig = px.scatter(
                vowel_df_original,
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
            fig.update_xaxes(autorange="reversed")
            fig.update_yaxes(autorange="reversed")

            self.configure_legend(fig)
            return fig, vowel_df_original

        except Exception as e:
            logging.error("Error while plotting vowel chart: %s", e, exc_info=True)
            raise ValueError(f"Failed to plot vowel chart: {e}")

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
        df_sorted = df_plot.sort_values(by="cosine_similarity", ascending=False)
        return fig, df_sorted

    def create_plotly_table(self, dataframe):
        """
        Create a Plotly table from a pandas DataFrame.
        Args:
            dataframe (pd.DataFrame): The data to display in the table.
        Returns:
            str: HTML string of the Plotly table.
        """
        try:
            col_widths = []
            for col in dataframe.columns:
                # Get max length of column name and values
                header_length = len(str(col))
                max_content_length = dataframe[col].astype(str).str.len().max()
                col_widths.append(max(header_length, max_content_length) * 8 + 20)

            fig = go.Figure(data=[go.Table(
                header=dict(
                    values=list(dataframe.columns),
                    fill_color='lavender',
                    align='left'
                ),
                cells=dict(
                    values=[dataframe[col] for col in dataframe.columns],
                    fill_color='aliceblue',
                    align='left'
                ),
                columnwidth=col_widths
            )])

            fig.update_layout(
                autosize=True,
                margin=dict(l=10, r=10, t=30, b=10),
                template='simple_white',
            )

            html = fig.to_html(include_plotlyjs='cdn', full_html=False, config=dict(displaylogo=False))

            return html

        except Exception as e:
            logging.error("Error creating Plotly table: %s", e, exc_info=True)
            raise
