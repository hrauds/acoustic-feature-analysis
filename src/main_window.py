import os
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QFileDialog, QVBoxLayout,
    QMessageBox, QListWidget, QAbstractItemView, QSplitter,
    QListWidgetItem, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.opensmile_features import OpenSmileFeatures
from src.visualization import Visualization
from src.formant_analysis import FormantAnalysis
from src.database import Database


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_files = []
        self.features_dict = {}
        self.formant_dict = {}
        self.opensmile_features = OpenSmileFeatures()
        self.visualization = Visualization()
        self.formant_analysis = FormantAnalysis()
        self.init_ui()
        self.database = Database()

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

        self.radar_btn = QPushButton("Radar")
        self.radar_btn.clicked.connect(self.visualize_radar)

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
        control_layout.addWidget(self.radar_btn)

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
                file_item = QListWidgetItem(os.path.basename(f))
                file_item.setData(Qt.UserRole, f)
                self.file_list_widget.addItem(file_item)

            self.extract_features()
        else:
            self.selected_files = []
            self.file_list_widget.clear()
            self.feature_list.clear()
            self.features_dict.clear()
            self.formant_dict.clear()

    def extract_features(self):
        self.features_dict = {}
        try:
            for f in self.selected_files:
                features = self.opensmile_features.process_file(f)
                speaker_label = os.path.basename(f)
                self.features_dict[speaker_label] = features

            all_features = set()
            for features_df in self.features_dict.values():
                all_features.update(features_df.columns.tolist())
            self.feature_list.addItems(sorted(all_features))

            QMessageBox.information(self, 'Success', "Feature extraction completed.")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Feature extraction failed: {str(e)}")

    def extract_formants(self):
        selected_files = self.file_list_widget.selectedItems()
        if not selected_files:
            QMessageBox.warning(self, 'Error', "Please select files to process.")
            return

        self.formant_dict = {}
        try:
            for file_item in selected_files:
                file_path = file_item.data(Qt.UserRole)
                speaker_label = os.path.basename(file_path)
                formant_df = self.formant_analysis.extract_formants(file_path)
                self.formant_dict[speaker_label] = formant_df

            self.visualize_vowel_chart()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Formant extraction failed: {str(e)}")

    def visualize_vowel_chart(self):
        if not self.formant_dict:
            QMessageBox.warning(self, 'Error', "Formant data is missing.")
            return

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111)

        table_data_raw, table_data_normalized = self.visualization.plot_vowel_chart(
            ax, self.formant_dict
        )
        self.canvas.draw()

        self.create_table(table_data_raw, self.raw_data_table)
        self.create_table(table_data_normalized, self.normalized_data_table)

    def visualize_time_line(self):
        selected_features = [item.text() for item in self.feature_list.selectedItems()]
        selected_files = self.file_list_widget.selectedItems()
        if not self.features_dict or not selected_files or not selected_features:
            QMessageBox.warning(self, 'Error', "Please select files and features to visualize.")
            return

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111)

        all_table_data = self.visualization.plot_time_series(
            ax, self.features_dict, selected_files, selected_features
        )
        self.canvas.draw()

        if all_table_data is not None:
            self.create_table(all_table_data, self.raw_data_table)

    def visualize_histogram(self):
        if not self.features_dict:
            QMessageBox.warning(self, 'Error', "Feature data is missing.")
            return

        selected_features = self.feature_list.selectedItems()
        if not selected_features or len(selected_features) != 1:
            QMessageBox.warning(self, 'Error', "Please select one feature for the histogram.")
            return

        self.clear_visualisation()
        selected_feature = selected_features[0].text()
        ax = self.canvas.figure.add_subplot(111)

        table_data = self.visualization.plot_histogram(
            ax, self.features_dict, selected_feature
        )
        self.canvas.draw()

        if table_data is not None:
            self.create_table(table_data, self.raw_data_table)

    def visualize_boxplot(self):
        if not self.features_dict:
            QMessageBox.warning(self, 'Error', "Feature data is missing.")
            return

        selected_features = self.feature_list.selectedItems()
        if not selected_features or len(selected_features) != 1:
            QMessageBox.warning(self, 'Error', "Please select one feature for the boxplot.")
            return

        self.clear_visualisation()
        selected_feature = selected_features[0].text()
        ax = self.canvas.figure.add_subplot(111)

        summary_table = self.visualization.plot_boxplot(
            ax, self.features_dict, selected_feature
        )
        self.canvas.draw()

        if summary_table is not None:
            self.create_table(summary_table, self.raw_data_table)

    def visualize_radar(self):
        if not self.features_dict:
            QMessageBox.warning(self, 'Error', "Feature data is missing.")
            return

        selected_features = [item.text() for item in self.feature_list.selectedItems()]
        if not selected_features:
            QMessageBox.warning(self, 'Error', "Please select features for the radar chart.")
            return

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111, polar=True)

        radar_df_original, radar_df_normalized = self.visualization.plot_radar_chart(
            ax, self.features_dict, selected_features
        )
        self.canvas.draw()

        if radar_df_original is not None:
            self.create_table(radar_df_original, self.raw_data_table)
        if radar_df_normalized is not None:
            self.create_table(radar_df_normalized, self.normalized_data_table)

    def create_table(self, dataframe, table_widget):
        table_widget.setRowCount(len(dataframe))
        table_widget.setColumnCount(len(dataframe.columns))
        table_widget.setHorizontalHeaderLabels(dataframe.columns)

        for row in range(len(dataframe)):
            for col in range(len(dataframe.columns)):
                value = str(dataframe.iat[row, col])
                table_widget.setItem(row, col, QTableWidgetItem(value))

    def clear_visualisation(self):
        self.canvas.figure.clear()
        self.raw_data_table.clearContents()
        self.raw_data_table.setRowCount(0)
        self.raw_data_table.setColumnCount(0)
        self.normalized_data_table.clearContents()
        self.normalized_data_table.setRowCount(0)
        self.normalized_data_table.setColumnCount(0)
