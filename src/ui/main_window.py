from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QFileDialog, QVBoxLayout,
    QMessageBox, QListWidget, QAbstractItemView, QSplitter,
    QTableWidget, QTableWidgetItem, QListWidgetItem
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.ui.visualization import Visualization
from src.database import Database
from src.speech_importer import SpeechImporter


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.visualization = Visualization()
        self.init_ui()
        self.database = Database()
        self.speech_importer = SpeechImporter()

        self.load_existing_recordings()

    def init_ui(self):
        self.setWindowTitle("Speech Analysis Application")
        self.setGeometry(100, 100, 1200, 600)

        # Upload
        self.label = QLabel("Upload audio and TextGrid files:", self)
        self.label.setAlignment(Qt.AlignCenter)

        self.upload_btn = QPushButton("Import Files", self)
        self.upload_btn.clicked.connect(self.upload_files)

        # List imported files
        self.file_list_widget = QListWidget(self)
        self.file_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.file_list_widget.itemSelectionChanged.connect(self.on_recording_selection_changed)

        self.feature_label = QLabel("Available Features:", self)
        self.feature_label.setAlignment(Qt.AlignCenter)

        self.feature_list = QListWidget(self)
        self.feature_list.setSelectionMode(QAbstractItemView.MultiSelection)

        # Buttons for different visualizations
        self.vowel_chart_btn = QPushButton("Vowel Chart")
        # self.vowel_chart_btn.clicked.connect(self.extract_formants)

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
        control_layout.addWidget(QLabel("Available Recordings:"))
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

    def load_existing_recordings(self):
        """
        Load existing recordings from the database and display them in the file list widget.
        """
        self.file_list_widget.clear()
        try:
            recordings = self.database.get_all_recordings()
            for recording_id in recordings:
                file_item = QListWidgetItem(recording_id)
                self.file_list_widget.addItem(file_item)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to load recordings from database: {str(e)}")

    def upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio and TextGrid Files", "", "Audio and TextGrid Files (*.wav *.TextGrid);;All Files (*)"
        )

        if files:
            try:
                # Pass the list of files to SpeechImporter
                missing_pairs = self.speech_importer.import_files(files)

                # Reload the recordings list
                self.load_existing_recordings()

                if missing_pairs:
                    QMessageBox.warning(
                        self,
                        'Warning',
                        f"The following files are missing their pairs: {', '.join(missing_pairs)}"
                    )

                QMessageBox.information(self, 'Success', "File import completed.")
            except Exception as e:
                QMessageBox.critical(self, 'Error', f"File import failed: {str(e)}")
        else:
            QMessageBox.information(self, 'Info', "No files selected for import.")

    def on_recording_selection_changed(self):
        selected_items = self.file_list_widget.selectedItems()
        if selected_items:
            recording_ids = [item.text() for item in selected_items]
            self.features_dict = self.database.get_features_for_recordings(recording_ids)
            self.update_feature_list()
        else:
            self.features_dict = {}
            self.feature_list.clear()

    def update_feature_list(self):
        """
        Update the feature list based on the fetched features.
        """
        all_features = set()
        for features_list in self.features_dict.values():
            for feature_dict in features_list:
                all_features.update(feature_dict.keys())
        # Remove unnecessary keys
        unnecessary_keys = {'_id', 'recording_id', 'interval_type', 'start', 'end', 'text'}
        all_features -= unnecessary_keys
        self.feature_list.clear()
        self.feature_list.addItems(sorted(all_features))

    def visualize_time_line(self):
        selected_features = [item.text() for item in self.feature_list.selectedItems()]
        if not self.features_dict or not selected_features:
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111)

        # Call the visualization method with database features
        all_table_data = self.visualization.plot_time_series(
            ax, self.features_dict, selected_features
        )
        self.canvas.draw()

        if all_table_data is not None:
            self.create_table(all_table_data, self.raw_data_table)

    def visualize_histogram(self):
        selected_features = self.feature_list.selectedItems()
        if not self.features_dict or not selected_features or len(selected_features) != 1:
            QMessageBox.warning(self, 'Error', "Please select one feature to visualize.")
            return

        selected_feature = selected_features[0].text()

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111)

        table_data = self.visualization.plot_histogram(
            ax, self.features_dict, selected_feature
        )
        self.canvas.draw()

        if table_data is not None:
            self.create_table(table_data, self.raw_data_table)

    def visualize_boxplot(self):
        selected_features = self.feature_list.selectedItems()
        if not self.features_dict or not selected_features or len(selected_features) != 1:
            QMessageBox.warning(self, 'Error', "Please select one feature to visualize.")
            return

        selected_feature = selected_features[0].text()

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111)

        summary_table = self.visualization.plot_boxplot(
            ax, self.features_dict, selected_feature
        )
        self.canvas.draw()

        if summary_table is not None:
            self.create_table(summary_table, self.raw_data_table)

    def visualize_radar(self):
        selected_features = [item.text() for item in self.feature_list.selectedItems()]
        if not self.features_dict or not selected_features:
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
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
        table_widget.clearContents()
        table_widget.setRowCount(0)
        table_widget.setColumnCount(0)

        if dataframe.empty:
            return

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
        self.canvas.draw()
