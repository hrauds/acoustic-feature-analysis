import sys
import os
import logging

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFileDialog,
    QVBoxLayout, QMessageBox, QListWidget, QAbstractItemView, QSplitter, QListWidgetItem
)
from PyQt5.QtCore import Qt
from matplotlib import patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import opensmile
import parselmouth
import numpy as np
import pandas as pd
import matplotlib as plt
import seaborn as sns


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
        self.setGeometry(100, 100, 1000, 600)

        # labels, buttons
        self.label = QLabel("Upload audio files:", self)
        self.label.setAlignment(Qt.AlignCenter)

        self.upload_btn = QPushButton("Upload Files", self)
        self.upload_btn.clicked.connect(self.upload_files)

        # list extracted features
        self.file_list_widget = QListWidget(self)
        self.file_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)

        self.feature_label = QLabel("Available Features:", self)
        self.feature_label.setAlignment(Qt.AlignCenter)

        self.feature_list = QListWidget(self)
        self.feature_list.setSelectionMode(QAbstractItemView.MultiSelection)

        self.vowel_chart_btn = QPushButton("Vowel Chart")
        self.vowel_chart_btn.clicked.connect(self.extract_formants)

        self.time_line_btn = QPushButton("Time Line Graph")
        self.time_line_btn.clicked.connect(self.visualize_time_line)

        self.histogram_btn = QPushButton("Histogram")
        self.histogram_btn.clicked.connect(self.visualize_histogram)

        self.boxplot_btn = QPushButton("Boxplot")
        self.boxplot_btn.clicked.connect(self.visualize_boxplot)

        # visualization canvas
        self.canvas = FigureCanvas(Figure())

        splitter = QSplitter(Qt.Vertical)

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

        visualization_panel = QWidget()
        visualization_layout = QVBoxLayout(visualization_panel)
        visualization_layout.addWidget(self.canvas)

        splitter.addWidget(control_panel)
        splitter.addWidget(visualization_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "", "Audio Files (*.wav);;All Files (*)"
        )

        if files:
            self.selected_files = files
            self.file_list_widget.clear()
            for f in files:
                item = QListWidgetItem(os.path.basename(f))
                item.setData(Qt.UserRole, f)
                self.file_list_widget.addItem(item)

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
        print(self.features_dict.keys())

        try:
            for f in self.selected_files:
                features = self.smile.process_file(f)
                speaker_label = os.path.basename(f)
                self.features_dict[speaker_label] = features

            # update the feature list with available features
            all_features = set()
            for features_df in self.features_dict.values():
                all_features.update(features_df.columns.tolist())
                print(features_df.head())
            self.feature_list.addItems(sorted(all_features))

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
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Error', "Please select files to process.")
            return

        self.formant_dict = {}

        try:
            for item in selected_items:
                file_path = item.data(Qt.UserRole)

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

        print(features_df[['F1', 'F2', 'zsc_F1', 'zsc_F2']].head())

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
                    horizontalalignment = 'left', fontsize=12, color='black', fontweight='bold'
                )

        ax.invert_xaxis()
        ax.invert_yaxis()

        ax.set_xlabel("F2 (Hz)")
        ax.set_ylabel("F1 (Hz)")

        ax.set_title("Vowel Chart")

        self.canvas.draw()

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
        if not self.features_dict:
            QMessageBox.warning(self, 'Error', "Feature data is missing.")
            return

        selected_features = [item.text() for item in self.feature_list.selectedItems()]
        if not selected_features:
            QMessageBox.warning(self, 'Error', "Please select feature(s) to visualize.")
            return

        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Error', "Please select files to visualize.")
            return

        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)

        colors = ['blue', 'green', 'red', 'purple', 'orange', 'brown', 'pink', 'gray']

        color_index = 0

        for item in selected_items:
            speaker_label = os.path.basename(item.data(Qt.UserRole))
            features_df = self.features_dict.get(speaker_label)
            print(features_df.head())
            if features_df is None:
                continue
            for feature in selected_features:
                if feature not in features_df.columns:
                    continue

                if 'start' in features_df.index.names:
                    time_index = features_df.index.get_level_values('start').total_seconds()
                elif 'frameTime' in features_df.index.names:
                    time_index = features_df.index.get_level_values('frameTime')
                else:
                    time_index = np.arange(len(features_df))

                values = features_df[feature].values.flatten()
                ax.plot(time_index, values, label=f"{speaker_label} - {feature}",
                        color=colors[color_index % len(colors)])
                color_index += 1

        ax.set_title("Selected Features Over Time")
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Feature Value")
        ax.legend()

        self.canvas.draw()

    def visualize_histogram(self):
        if not self.features_dict:
            QMessageBox.warning(self, 'Error', "Feature data is missing.")
            return

        selected_items = self.feature_list.selectedItems()
        if not selected_items or len(selected_items) != 1:
            QMessageBox.warning(self, 'Error', "Please select one feature for histogram.")
            return

        selected_feature = selected_items[0].text()

        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)  # clears the current figure on the canvas
        # adds a new subplot (ax) 111 means a single plot area (1 row, 1 column).

        colors = ['blue', 'green', 'red', 'purple', 'orange', 'brown', 'pink', 'gray']

        for idx, (speaker_label, features_df) in enumerate(self.features_dict.items()):
            if selected_feature not in features_df.columns:
                print(features_df.head())
                continue
            ax.hist(features_df[selected_feature].values.flatten(), bins=30, alpha=0.5,
                    label=speaker_label, color=colors[idx % len(colors)])

        ax.set_xlabel(selected_feature)
        ax.set_ylabel('Frequency')
        ax.set_title(f'{selected_feature} Histogram Comparison')
        ax.legend()

        self.canvas.draw()

    def visualize_boxplot(self):
        if not self.features_dict:
            QMessageBox.warning(self, 'Error', "Feature data is missing.")
            return

        selected_items = self.feature_list.selectedItems()
        if not selected_items or len(selected_items) != 1:
            QMessageBox.warning(self, 'Error', "Please select one feature for boxplot.")
            return

        selected_feature = selected_items[0].text()

        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)

        data = []
        labels = []
        for speaker_label, features_df in self.features_dict.items():
            print(features_df.head())
            if selected_feature in features_df.columns:
                data.append(features_df[selected_feature].dropna().values.flatten())
                labels.append(speaker_label)

        ax.boxplot(data, labels=labels, vert=True)
        ax.set_ylabel(selected_feature)
        ax.set_title(f'{selected_feature} Boxplot Comparison')

        self.canvas.draw()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
    app = QApplication(sys.argv)
    window = OpenSmileApp()
    window.show()
    sys.exit(app.exec_())
