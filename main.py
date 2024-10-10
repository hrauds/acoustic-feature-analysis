import sys
import os

import logging
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFileDialog,
    QVBoxLayout, QMessageBox, QListWidget, QAbstractItemView
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import opensmile


class OpenSmileApp(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_file = None
        self.features_df = None
        self.smile = opensmile.Smile(
            feature_set=opensmile.FeatureSet.eGeMAPSv02,
            feature_level=opensmile.FeatureLevel.LowLevelDescriptors
        )
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("OpenSMILE GeMAPS Feature Extractor")
        self.setGeometry(100, 100, 800, 600)

        self.label = QLabel("Upload an audio file:", self)
        self.label.setAlignment(Qt.AlignCenter)

        self.upload_btn = QPushButton("Upload File", self)
        self.upload_btn.clicked.connect(self.upload_file)

        self.file_label = QLabel("No file selected", self)
        self.file_label.setAlignment(Qt.AlignCenter)

        self.feature_label = QLabel("Select feature(s) to extract:", self)
        self.feature_label.setAlignment(Qt.AlignCenter)

        self.feature_list = QListWidget(self)
        self.feature_list.setSelectionMode(QAbstractItemView.MultiSelection)

        self.extract_btn = QPushButton("Extract Features", self)
        self.extract_btn.clicked.connect(self.extract_features)

        self.canvas = FigureCanvas(Figure(figsize=(5, 3)))

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.upload_btn)
        layout.addWidget(self.file_label)
        layout.addWidget(self.feature_label)
        layout.addWidget(self.feature_list)
        layout.addWidget(self.extract_btn)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

        self.populate_feature_list()

    def populate_feature_list(self):
        features = self.smile.feature_names
        self.feature_list.addItems(features)

    def upload_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "", "Audio Files (*.wav);;All Files (*)"
        )

        if file_name:
            self.selected_file = file_name
            self.file_label.setText("Selected file: " + str(os.path.basename(file_name)))
        else:
            self.file_label.setText("No file selected")

    def extract_features(self):
        if not self.selected_file:
            QMessageBox.warning(self, 'Error', "Please upload a file first.")
            return

        try:
            features = self.smile.process_file(self.selected_file)
            self.features_df = features
            self.visualize_features()
        except Exception as e:
            QMessageBox.critical(self, 'Error', "Feature extraction failed: " + str(e))

    def visualize_features(self):
        if self.features_df is None:
            QMessageBox.warning(self, 'Error', "No features extracted.")
            return

        selected_items = self.feature_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Error', "Please select at least one feature to visualize.")
            return

        selected_features = [item.text() for item in selected_items]
        missing_features = [
            feat for feat in selected_features if feat not in self.features_df.columns
        ]

        if missing_features:
            QMessageBox.warning(self, 'Error', "The following features are not found: " + str(missing_features))
            return

        time_seconds = self.features_df.index.get_level_values('start').total_seconds()
        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)

        for feature in selected_features:
            ax.plot(time_seconds, self.features_df[feature], label=feature)

        ax.set_title("Selected Features Over Time")
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Feature Value")
        ax.legend()

        self.canvas.draw()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication(sys.argv)
    window = OpenSmileApp()
    window.show()
    sys.exit(app.exec_())
