import math
import sys
import os
import logging

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFileDialog,
    QVBoxLayout, QMessageBox, QListWidget, QAbstractItemView, QSplitter, QListWidgetItem, QTableView, QTableWidgetItem,
    QTableWidget
)
from PyQt5.QtCore import Qt
from matplotlib import patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import opensmile
import parselmouth
import numpy as np
import pandas as pd
import seaborn as sns
import math



class OpenSmileApp(QWidget):
    pd.set_option('display.max_columns', None)
    pd.set_option('display.expand_frame_repr', False)

    def __init__(self):
        super().__init__()
        self.selected_files = []
        self.features_dict = {}
        self.formant_dict = {}
        self.smile = opensmile.Smile(
            feature_set=opensmile.FeatureSet.eGeMAPSv02,
            feature_level=opensmile.FeatureLevel.LowLevelDescriptors
        )
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("OpenSMILE GeMAPS Feature Extractor")
        self.setGeometry(100, 100, 1200, 600)

        # Upload
        self.label = QLabel("Upload audio files:", self)
        self.label.setAlignment(Qt.AlignCenter)

        self.upload_btn = QPushButton("Upload Files", self)
        self.upload_btn.clicked.connect(self.upload_files)

        # List extracted features
        self.file_list_widget = QListWidget(self)
        self.file_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)

        self.feature_label = QLabel("Available Features:", self)
        self.feature_label.setAlignment(Qt.AlignCenter)

        self.feature_list = QListWidget(self)
        self.feature_list.setSelectionMode(QAbstractItemView.MultiSelection)

        # Buttons for different visualizations
        self.vowel_chart_btn = QPushButton("Vowel Chart")
        self.vowel_chart_btn.clicked.connect(self.extract_formants)

        self.time_line_btn = QPushButton("Time Line Graph")
        self.time_line_btn.clicked.connect(self.visualize_time_line)

        self.histogram_btn = QPushButton("Histogram")
        self.histogram_btn.clicked.connect(self.visualize_histogram)

        self.boxplot_btn = QPushButton("Boxplot")
        self.boxplot_btn.clicked.connect(self.visualize_boxplot)

        # Visualization canvas
        self.canvas = FigureCanvas(Figure())

        # Control panel layout
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.addWidget(self.label)
        control_layout.addWidget(self.upload_btn)
        control_layout.addWidget(QLabel("Selected Files:"))
        control_layout.addWidget(self.file_list_widget)
        control_layout.addWidget(self.feature_label)
        control_layout.addWidget(self.feature_list)
        control_layout.addWidget(self.vowel_chart_btn)
        control_layout.addWidget(self.time_line_btn)
        control_layout.addWidget(self.histogram_btn)
        control_layout.addWidget(self.boxplot_btn)

        # Visualization panel and data panel split
        vis_data_splitter = QSplitter(Qt.Horizontal)

        # Visualization panel
        visualization_panel = QWidget()
        visualization_layout = QVBoxLayout(visualization_panel)
        visualization_layout.addWidget(self.canvas)

        # Data tables panel
        self.raw_data_table = QTableWidget(self)
        self.normalized_data_table = QTableWidget(self)
        raw_data_label = QLabel("Raw Data", self)
        normalized_data_label = QLabel("Normalized Data", self)
        data_tables_panel = QWidget()
        data_tables_layout = QVBoxLayout(data_tables_panel)
        data_tables_layout.addWidget(raw_data_label)
        data_tables_layout.addWidget(self.raw_data_table)
        data_tables_layout.addWidget(normalized_data_label)
        data_tables_layout.addWidget(self.normalized_data_table)

        # Visualization and data panels split
        vis_data_splitter.addWidget(visualization_panel)
        vis_data_splitter.addWidget(data_tables_panel)
        vis_data_splitter.setStretchFactor(0, 2)
        vis_data_splitter.setStretchFactor(1, 1)

        # Main layout
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(control_panel)
        main_splitter.addWidget(vis_data_splitter)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)

        main_layout = QVBoxLayout()
        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

    def upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "", "Audio Files (*.wav);;All Files (*)"
        )

        if files:
            self.selected_files = files
            self.file_list_widget.clear()
            for f in files:
                file = QListWidgetItem(os.path.basename(f))
                file.setData(Qt.UserRole, f)
                self.file_list_widget.addItem(file)

            self.extract_features()
        else:
            self.selected_files = []
            self.file_list_widget.clear()
            self.feature_list.clear()
            self.features_dict.clear()
            self.formant_dict.clear()

    def extract_features(self):
        self.features_dict = {}
        self.feature_list.clear()

        try:
            for f in self.selected_files:
                features = self.smile.process_file(f)
                speaker_label = os.path.basename(f)
                self.features_dict[speaker_label] = features

            # update the feature list with available features
            all_features = set()
            for features_df in self.features_dict.values():
                all_features.update(features_df.columns.tolist())
            self.feature_list.addItems(sorted(all_features))
            print()

            QMessageBox.information(self, 'Success', "Feature extraction completed.")
        except Exception as e:
            QMessageBox.critical(self, 'Error', "Feature extraction failed: " + str(e))

    def classify_vowel(self, f1, f2):
        """ Simplified vowel classification for testing. Based on F1 and F2 frequency ranges. """
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

    def extract_formants(self):
        selected_files = self.file_list_widget.selectedItems()
        if not selected_files:
            QMessageBox.warning(self, 'Error', "Please select files to process.")
            return

        self.formant_dict = {}

        try:
            for file in selected_files:
                file_path = file.data(Qt.UserRole)

                f1_list, f2_list, times = self.get_formants(file_path)

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

                speaker_label = os.path.basename(file_path)
                self.formant_dict[speaker_label] = formant_df

            self.visualize_vowel_chart()

        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Formant extraction failed: {str(e)}")

    def get_formants(self, file_path, time_step=0.01):
        """
        Extract F1 and F2 formants using Praat's Burg method.
        Returns lists of F1, F2 values and corresponding time stamps.
        """
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

        return f1_list, f2_list, times

    def barkify(self, data, formants):
        """https://lingmethodshub.github.io/content/python/vowel-plotting-py/"""
        # For each formant listed, make a copy of the column prefixed with z
        for formant in formants:
            for ch in formant:
                if ch.isnumeric():
                    num = ch
            formantchar = (formant.split(num)[0])
            name = str(formant).replace(formantchar, 'z')
            # Convert each value from Hz to Bark
            data[name] = 26.81 / (1 + 1960 / data[formant]) - 0.53
        return data

    def Lobify(self, data, formants):
        """https://lingmethodshub.github.io/content/python/vowel-plotting-py/"""
        zscore = lambda x: (x - x.mean()) / x.std()
        for formant in formants:
            name = str("zsc_" + formant)
            data[name] = zscore(data[formant])
        return data

    def normalize_vowels(self, features_df):
        """
        Normalizes the vowel formants using the Lobanov method.
        Assumes features_df has columns like 'F1', 'F2'.
        """
        formants = ['F1', 'F2']

        # Convert formants to Bark scale
        # features_df = self.barkify(features_df, formants)

        # Normalize formants using Lobanov normalization
        features_df = self.Lobify(features_df, formants)
        return features_df

    def visualize_vowel_chart(self):
        if not self.formant_dict:
            QMessageBox.warning(self, 'Error', "Formant data is missing.")
            return

        self.canvas.figure.clear()

        sns.set(style='ticks', context='notebook')

        ax = self.canvas.figure.add_subplot(111)

        speaker_colors = sns.color_palette("husl", len(self.formant_dict))

        for speaker_idx, (speaker_label, formant_df) in enumerate(self.formant_dict.items()):
            norm_formant_df = self.normalize_vowels(formant_df)

            sns.scatterplot(
                x='F2',
                y='F1',
                data=norm_formant_df,
                color=speaker_colors[speaker_idx],
                alpha=0.7,
                ax=ax
            )

            for _, row in norm_formant_df.iterrows():
                ax.text(
                    row['F2'] + 0.1, row['F1'], row['Vowel'],
                    horizontalalignment='left', fontsize=12, color='black', fontweight='bold'
                )

        ax.invert_xaxis()
        ax.invert_yaxis()

        ax.set_xlabel("F2 (Hz)")
        ax.set_ylabel("F1 (Hz)")
        ax.set_title("Vowel Chart")

        self.canvas.draw()

        self.create_table(formant_df[['Time', 'F1', 'F2', 'Vowel']], self.raw_data_table)
        self.create_table(norm_formant_df[['Time', 'zsc_F1', 'zsc_F2', 'Vowel']], self.normalized_data_table)

    def plot_ellipse(self, x_data, y_data, ax, color='blue'):
        mean_x = np.mean(x_data)
        mean_y = np.mean(y_data)
        std_x = np.std(x_data)
        std_y = np.std(y_data)

        width = 2 * std_x
        height = 2 * std_y

        ellipse = patches.Ellipse((mean_x, mean_y), width, height, angle=0, color=color, alpha=0.3, fill=True)
        ax.add_patch(ellipse)

    def visualize_time_line(self):
        if not self.features_dict or not self.file_list_widget.selectedItems() or not self.feature_list.selectedItems():
            QMessageBox.warning(self, 'Error', "Please select files and features to visualize.")
            return

        selected_features = [item.text() for item in self.feature_list.selectedItems()]
        selected_files = self.file_list_widget.selectedItems()

        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)
        colors = ['blue', 'green', 'red', 'purple', 'orange', 'brown', 'pink', 'gray']

        all_table_data = []

        for idx, file in enumerate(selected_files):
            speaker_label = os.path.basename(file.data(Qt.UserRole))
            features_df = self.features_dict.get(speaker_label)

            if features_df is None:
                continue

            time_index = features_df.index.get_level_values('start').total_seconds()
            speaker_data = pd.DataFrame({'Time': time_index})

            for feature in selected_features:
                if feature in features_df.columns:
                    ax.plot(time_index, features_df[feature].values, label=f"{speaker_label} - {feature}",
                            color=colors[idx % len(colors)])

                    speaker_data[f'{feature} - {speaker_label}'] = features_df[feature].values

            all_table_data.append(speaker_data)

        ax.set_title("Selected Features Over Time")
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Feature Value")
        ax.legend()
        self.canvas.draw()

        if all_table_data:
            combined_data = pd.concat(all_table_data, axis=1)
            combined_data = combined_data.loc[:, ~combined_data.columns.duplicated()]
            self.create_table(combined_data, self.raw_data_table)

    def visualize_histogram(self):
        if not self.features_dict:
            QMessageBox.warning(self, 'Error', "Feature data is missing.")
            return

        selected_features = self.feature_list.selectedItems()
        if not selected_features or len(selected_features) != 1:
            QMessageBox.warning(self, 'Error', "Please select one feature for the histogram.")
            return

        selected_feature = selected_features[0].text()

        all_values = [features_df[selected_feature].values.flatten()
                      for features_df in self.features_dict.values()
                      if selected_feature in features_df.columns]

        if not all_values:
            QMessageBox.warning(self, 'Error', "Selected feature not found in the data.")
            return

        all_values = np.concatenate(all_values)

        # Calculate the number of bins dynamically using Sturges' rule
        num_bins = int(1 + math.log2(len(all_values))) if len(all_values) > 0 else 10
        bins = np.linspace(all_values.min(), all_values.max(), num_bins + 1)

        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)

        all_speaker_data = {}

        for speaker_label, features_df in self.features_dict.items():
            if selected_feature in features_df.columns:
                feature_values = features_df[selected_feature].values.flatten()
                ax.hist(feature_values, bins=bins, alpha=0.5, label=speaker_label)

                hist_values, _ = np.histogram(feature_values, bins=bins)
                all_speaker_data[speaker_label] = hist_values

        ax.set_xlabel(f"{selected_feature}")
        ax.set_ylabel("Frequency")
        ax.set_title(f'{selected_feature} Histogram')
        ax.legend()

        self.canvas.draw()

        bin_labels = []
        for i in range(len(bins) - 1):
            lower_bound = bins[i]
            upper_bound = bins[i + 1]
            label = f'{lower_bound: .2f} to {upper_bound: .2f}'
            bin_labels.append(label)
        table_data = pd.DataFrame.from_dict(all_speaker_data, orient='index', columns=bin_labels)

        table_data.insert(0, 'Speaker', table_data.index)

        self.create_table(table_data, self.raw_data_table)

    def visualize_boxplot(self):
        if not self.features_dict:
            QMessageBox.warning(self, 'Error', "Feature data is missing.")
            return

        selected_files = self.feature_list.selectedItems()
        if not selected_files or len(selected_files) != 1:
            QMessageBox.warning(self, 'Error', "Please select one feature for the boxplot.")
            return

        selected_feature = selected_files[0].text()

        self.canvas.figure.clear()
        self.canvas.figure.set_size_inches(10, 8)
        ax = self.canvas.figure.add_subplot(111)

        data = []
        labels = []
        boxplot_table_data = []

        for speaker_label, features_df in self.features_dict.items():
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
            QMessageBox.warning(self, 'Error', "No data available for the selected feature.")
            return

        ax.boxplot(data, labels=labels, vert=True, patch_artist=True, whis=2.0,
                   boxprops=dict(facecolor='lightblue', color='blue'),
                   medianprops=dict(color='red'))
        ax.set_ylabel(f'{selected_feature}')
        ax.set_xlabel('Speakers')
        ax.set_title(f'{selected_feature} Boxplot')
        ax.grid(True)

        self.canvas.figure.tight_layout(pad=3.0)  # pad for extra space
        self.canvas.draw()

        summary_table = pd.DataFrame(boxplot_table_data)
        summary_table = summary_table[['Speaker', 'Min', 'Q1', 'Median', 'Q3', 'Max']]
        self.create_table(summary_table, self.raw_data_table)

    def create_table(self, dataframe, table_widget):
        self.raw_data_table.clearContents()
        self.normalized_data_table.clearContents()

        table_widget.setRowCount(len(dataframe))
        table_widget.setColumnCount(len(dataframe.columns))

        table_widget.setHorizontalHeaderLabels(dataframe.columns)

        for row in range(len(dataframe)):
            for col in range(len(dataframe.columns)):
                value = str(dataframe.iat[row, col])
                table_widget.setItem(row, col, QTableWidgetItem(value))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
    app = QApplication(sys.argv)
    window = OpenSmileApp()
    window.show()
    sys.exit(app.exec_())
