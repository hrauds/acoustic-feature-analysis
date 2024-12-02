from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QFileDialog, QVBoxLayout,
    QMessageBox, QListWidget, QAbstractItemView, QSplitter,
    QTableWidget, QTableWidgetItem, QListWidgetItem, QRadioButton, QButtonGroup
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

        self.filtered_features = {}
        self.features = {}

    def init_ui(self):
        self.setWindowTitle("Speech Analysis Application")
        self.setGeometry(100, 100, 1400, 700)

        # Upload Section
        self.label = QLabel("Upload audio and TextGrid files:", self)
        self.label.setAlignment(Qt.AlignCenter)

        self.upload_btn = QPushButton("Import Files", self)
        self.upload_btn.clicked.connect(self.upload_files)

        # List imported files
        self.file_list_widget = QListWidget(self)
        self.file_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.file_list_widget.itemSelectionChanged.connect(self.on_recording_selection_changed)

        # Analysis level selection
        self.analysis_label = QLabel("Select Analysis Level:", self)
        self.analysis_label.setAlignment(Qt.AlignCenter)

        # Added "Recording" radio button
        self.recording_radio = QRadioButton("Recording")
        self.word_radio = QRadioButton("Word")
        self.phoneme_radio = QRadioButton("Phoneme")
        self.recording_radio.setChecked(True)  # Default selection

        self.analysis_group = QButtonGroup(self)
        self.analysis_group.addButton(self.recording_radio)
        self.analysis_group.addButton(self.word_radio)
        self.analysis_group.addButton(self.phoneme_radio)
        self.analysis_group.buttonClicked.connect(self.on_analysis_level_changed)

        # List specific items (words/phonemes)
        self.item_label = QLabel("Available Words/Phonemes:", self)
        self.item_label.setAlignment(Qt.AlignCenter)

        self.item_list = QListWidget(self)
        self.item_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.item_list.setVisible(False)  # Initially hidden
        self.item_label.setVisible(False)  # Initially hidden
        self.item_list.itemSelectionChanged.connect(self.on_item_selection_changed)

        # List available features
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

        # Analysis level selection
        control_layout.addWidget(self.analysis_label)
        control_layout.addWidget(self.recording_radio)
        control_layout.addWidget(self.word_radio)
        control_layout.addWidget(self.phoneme_radio)

        # Feature and item selection
        control_layout.addWidget(self.item_label)
        control_layout.addWidget(self.item_list)

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
        Load recordings from the database and display them in the file list widget.
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
            analysis_level = self.get_selected_analysis_level()

            # Get features for the selected recordings and analysis level
            self.features = self.database.get_features_for_recordings(recording_ids, analysis_level)

            # Update feature and item lists
            self.update_feature_list()
            self.update_item_list()

            if analysis_level == 'recording':
                self.filtered_features = self.features
            else:
                self.filtered_features = {}
        else:
            # Reset features and UI
            self.features = {}
            self.feature_list.clear()
            self.item_list.clear()
            self.item_label.setVisible(False)
            self.item_list.setVisible(False)
            self.filtered_features = {}

    def on_analysis_level_changed(self):
        """
        Update features and filtered_features when the analysis level changes.
        """
        selected_items = self.file_list_widget.selectedItems()
        analysis_level = self.get_selected_analysis_level()

        if selected_items:
            recording_ids = [item.text() for item in selected_items]
            self.features = self.database.get_features_for_recordings(recording_ids, analysis_level)

            if analysis_level == 'recording':
                self.filtered_features = self.features
            else:
                self.filtered_features = {}

            self.update_feature_list()
            self.update_item_list()
        else:
            self.features = {}
            self.feature_list.clear()
            self.item_list.clear()
            self.item_label.setVisible(False)
            self.item_list.setVisible(False)
            self.filtered_features = {}

    def get_selected_analysis_level(self):
        """
        Returns the currently selected analysis level.
        """
        if self.recording_radio.isChecked():
            return 'recording'
        elif self.phoneme_radio.isChecked():
            return 'phoneme'
        else:
            return 'word'

    def update_feature_list(self):
        """
        Update the feature list based on the fetched features.
        """
        all_features = set()

        for features_list in self.features.values():
            for feature_dict in features_list:
                if "mean" in feature_dict:
                    all_features.update(feature_dict["mean"].keys())

        self.feature_list.clear()
        if all_features:
            self.feature_list.addItems(all_features)
        else:
            print("No features found to populate the feature list.")

    def update_item_list(self):
        """
        Update the item list (words/phonemes) based on the fetched features and selected analysis level.
        """
        analysis_level = self.get_selected_analysis_level()
        self.item_list.clear()

        if analysis_level == 'recording':
            self.item_label.hide()
            self.item_list.hide()
            return

        items = set()
        for recording_id, features_list in self.features.items():
            for feature_dict in features_list:

                item_text = feature_dict.get('text', '').strip()
                if item_text:
                    combined_text = f"{recording_id} - {item_text}"
                    items.add(combined_text)

        self.item_list.clear()
        if items:
            self.item_list.addItems(items)
            self.item_label.show()
            self.item_list.show()
        else:
            self.item_label.hide()
            self.item_list.hide()

    def on_item_selection_changed(self):
        """
        Filter features based on selected items in the item list.
        """
        analysis_level = self.get_selected_analysis_level()

        if analysis_level == 'recording':
            # For recording-level, use all features without filtering by items
            self.filtered_features = self.features
        else:
            selected_items = self.item_list.selectedItems()
            if selected_items:
                selected_texts = [item.text().split(' - ')[1] for item in selected_items]
                self.filtered_features = {
                    recording_id: [
                        feature for feature in features if feature.get("text", "").strip() in selected_texts
                    ]
                    for recording_id, features in self.features.items()
                }
            else:
                self.filtered_features = {}

    def visualize_time_line(self):
        print("vii")
        print(self.filtered_features)
        if not self.filtered_features:
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111)

        # Call the visualization method
        all_table_data = self.visualization.plot_time_series(ax, self.filtered_features)
        self.canvas.draw()

        if all_table_data is not None:
            self.create_table(all_table_data, self.raw_data_table)

    def visualize_histogram(self):
        feature_count = sum(len(features) for features in self.filtered_features.values())
        if feature_count != 1:
            QMessageBox.warning(self, 'Error', "Please select one feature to visualize.")
            return

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111)

        # Call the visualization method
        table_data = self.visualization.plot_histogram(ax, self.filtered_features)
        self.canvas.draw()

        if table_data is not None:
            self.create_table(table_data, self.raw_data_table)

    def visualize_boxplot(self):
        feature_count = sum(len(features) for features in self.filtered_features.values())
        if feature_count != 1:
            QMessageBox.warning(self, 'Error', "Please select one feature to visualize.")
            return

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111)

        # Call the visualization method
        summary_table = self.visualization.plot_boxplot(ax, self.filtered_features)
        self.canvas.draw()

        if summary_table is not None:
            self.create_table(summary_table, self.raw_data_table)

    def visualize_radar(self):
        if not self.filtered_features:
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111, polar=True)

        # Call the visualization method
        radar_df_original, radar_df_normalized = self.visualization.plot_radar_chart(ax, self.filtered_features)
        self.canvas.draw()

        if radar_df_original is not None:
            self.create_table(radar_df_original, self.raw_data_table)
        if radar_df_normalized is not None:
            self.create_table(radar_df_normalized, self.normalized_data_table)

    def visualize_vowel_chart(self):
        if not self.filtered_features:
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111)

        # Call the visualization method
        vowel_chart_data = self.visualization.plot_vowel_chart(ax, self.filtered_features)
        self.canvas.draw()

        if vowel_chart_data is not None:
            self.create_table(vowel_chart_data, self.raw_data_table)

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

