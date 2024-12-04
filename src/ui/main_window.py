from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QFileDialog, QVBoxLayout,
    QMessageBox, QListWidget, QAbstractItemView, QSplitter,
    QTableWidget, QTableWidgetItem, QRadioButton, QButtonGroup, QListWidgetItem
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
        self.database = Database()
        self.speech_importer = SpeechImporter()
        self.cached_features = {}  # Cache for storing fetched features
        self.init_ui()
        self.load_existing_recordings()

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
        self.file_list_widget.itemSelectionChanged.connect(self.on_recordings_changed)

        # Analysis level selection
        self.analysis_label = QLabel("Select Analysis Level:", self)
        self.analysis_label.setAlignment(Qt.AlignCenter)

        # Radio buttons for analysis level
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
        self.item_list.itemSelectionChanged.connect(self.on_items_changed)

        # List available features
        self.feature_label = QLabel("Available Features:", self)
        self.feature_label.setAlignment(Qt.AlignCenter)

        self.feature_list = QListWidget(self)
        self.feature_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.feature_list.itemSelectionChanged.connect(self.on_features_changed)

        # Buttons for different visualizations
        self.vowel_chart_btn = QPushButton("Vowel Chart")
        # self.vowel_chart_btn.clicked.connect(self.visualize_vowel_chart)

        self.time_line_btn = QPushButton("Time Line Graph")
        self.time_line_btn.clicked.connect(self.visualize_time_line)

        self.histogram_btn = QPushButton("Histogram")
        self.histogram_btn.clicked.connect(self.visualize_histogram)

        self.boxplot_btn = QPushButton("Boxplot")
        self.boxplot_btn.clicked.connect(self.visualize_boxplot)

        self.radar_btn = QPushButton("Radar")
        self.radar_btn.clicked.connect(self.visualize_radar)

        # Initially disable visualization buttons
        self.disable_visualization_buttons()

        # Visualization canvas
        self.canvas = FigureCanvas(Figure())

        # Control panel layout
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)

        control_layout.addWidget(self.label)
        control_layout.addWidget(self.upload_btn)

        control_layout.addWidget(QLabel("Available Recordings:", self))
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

        # Visualization buttons
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

        # Add panels to splitter
        vis_data_splitter.addWidget(visualization_panel)
        vis_data_splitter.addWidget(data_tables_panel)
        vis_data_splitter.setStretchFactor(0, 2)
        vis_data_splitter.setStretchFactor(1, 1)

        # Main layout with splitter
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(control_panel)
        main_splitter.addWidget(vis_data_splitter)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)

        # Final layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

    def load_existing_recordings(self):
        self.file_list_widget.clear()
        try:
            recordings = self.database.get_all_recordings()
            for recording_id in recordings:
                file_item = QListWidgetItem(recording_id)
                self.file_list_widget.addItem(file_item)
            print(f"Loaded recordings: {recordings}")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to load recordings from database: {str(e)}")

    def upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio and TextGrid Files", "", "Audio and TextGrid Files (*.wav *.TextGrid);;All Files (*)"
        )

        if files:
            try:
                missing_pairs = self.speech_importer.import_files(files)
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

    def on_recordings_changed(self):
        self.update_feature_cache()
        self.update_feature_list()
        self.update_item_list()
        self.update_visualization_buttons()
        self.clear_visualisation()

    def on_analysis_level_changed(self):
        self.update_feature_cache()
        self.update_feature_list()
        self.update_item_list()
        self.update_visualization_buttons()
        self.clear_visualisation()

    def on_items_changed(self):
        self.update_feature_list()
        self.update_visualization_buttons()
        self.clear_visualisation()

    def on_features_changed(self):
        self.update_visualization_buttons()
        self.clear_visualisation()

    def get_selected_analysis_level(self):
        if self.recording_radio.isChecked():
            return 'recording'
        elif self.phoneme_radio.isChecked():
            return 'phoneme'
        else:
            return 'word'

    def get_current_selections(self):
        selected_recordings = [item.text() for item in self.file_list_widget.selectedItems()]
        analysis_level = self.get_selected_analysis_level()
        selected_items = [item.data(Qt.UserRole) for item in
                          self.item_list.selectedItems()] if analysis_level != 'recording' else []
        selected_features = [item.text() for item in self.feature_list.selectedItems()]
        return {
            'recordings': selected_recordings,
            'analysis_level': analysis_level,
            'items': selected_items,
            'features': selected_features
        }

    def update_feature_cache(self):
        selections = self.get_current_selections()
        selected_recordings = selections['recordings']
        analysis_level = selections['analysis_level']

        if not selected_recordings:
            self.cached_features = {}
            return

        try:
            self.cached_features = self.database.get_features_for_recordings(selected_recordings, analysis_level)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to fetch features: {str(e)}")
            self.cached_features = {}

    def fetch_filtered_features(self):
        # Get current selections from the UI
        selections = self.get_current_selections()
        selected_items = selections['items']
        selected_features = selections['features']

        # Create a copy of cached features
        all_features = self.cached_features.copy()

        # Get the selected analysis level
        analysis_level = selections['analysis_level']

        if analysis_level != 'recording' and selected_items:
            filtered_all_features = {}
            for rec_id, features in all_features.items():
                # Filter features that match selected items _id
                filtered_features = [
                    feature for feature in features
                    if feature.get("_id") in selected_items
                ]
                if filtered_features:
                    filtered_all_features[rec_id] = filtered_features

            all_features = filtered_all_features

        # If specific features are selected, further filter the features
        if selected_features:
            filtered = {}
            for rec_id, features in all_features.items():
                filtered_features = []
                for feature in features:
                    # Filter the mean dictionary to include only selected features
                    mean_filtered = {k: v for k, v in feature.get("mean", {}).items() if k in selected_features}

                    # Get feature names
                    feature_names_ordered = list(feature.get("mean", {}).keys())
                    feature_indices = [i for i, k in enumerate(feature_names_ordered) if k in selected_features]

                    # Filter frame_values to include only selected features
                    frame_values_filtered = []
                    for timestamp, values in feature.get("frame_values", []):
                        if values and feature_indices:
                            selected_values = [values[i] for i in feature_indices]
                            frame_values_filtered.append((timestamp, selected_values))
                        else:
                            frame_values_filtered.append((timestamp, []))

                    # Build the filtered feature dictionary
                    filtered_feature = {
                        "text": feature.get("text", ""),
                        "mean": mean_filtered,
                        "frame_values": frame_values_filtered
                    }
                    filtered_features.append(filtered_feature)

                if filtered_features:
                    filtered[rec_id] = filtered_features

            all_features = filtered
            print(f"Features after feature selection: {all_features}")

        return all_features

    def update_feature_list(self):
        all_features = set()

        selections = self.get_current_selections()
        selected_items = selections['items']
        analysis_level = selections['analysis_level']

        features = self.cached_features

        if not features:
            self.feature_list.blockSignals(True)
            self.feature_list.clear()
            self.feature_list.setEnabled(False)
            self.feature_list.blockSignals(False)
            return

        self.feature_list.setSelectionMode(QAbstractItemView.MultiSelection)

        if analysis_level != 'recording' and selected_items:
            for rec_id, feature_list in features.items():
                for feature in feature_list:
                    if feature.get("_id") in selected_items:
                        all_features.update(feature.get("mean", {}).keys())
        else:
            for feature_list in features.values():
                for feature in feature_list:
                    all_features.update(feature.get("mean", {}).keys())

        self.feature_list.blockSignals(True)
        self.feature_list.clear()
        self.feature_list.clearSelection()

        if all_features:
            sorted_features = sorted(all_features)
            self.feature_list.addItems(sorted_features)
            self.feature_list.setEnabled(True)
        else:
            self.feature_list.setEnabled(False)
        self.feature_list.blockSignals(False)

    def update_item_list(self):
        analysis_level = self.get_selected_analysis_level()

        self.item_list.blockSignals(True)
        self.item_list.clear()
        self.item_list.clearSelection()

        if analysis_level == 'recording':
            self.item_label.hide()
            self.item_list.hide()
            self.item_list.blockSignals(False)
            return

        features = self.cached_features

        if not features:
            self.item_label.hide()
            self.item_list.hide()
            self.item_list.blockSignals(False)
            return

        items_by_recording = []
        for rec_id, feature_list in features.items():
            recording_items = []
            for feature in feature_list:
                item_text = feature.get('text', '').strip()
                timestamp = feature.get('frame_values', [])[0][0] if feature.get('frame_values') else None
                if item_text and timestamp is not None:
                    feature_id = feature.get('_id')
                    recording_items.append((timestamp, f"{rec_id} - {item_text}", feature_id))

            recording_items = sorted(recording_items, key=lambda x: x[0])
            items_by_recording.extend(recording_items)

        if items_by_recording:
            for _, item_text, feature_id in items_by_recording:
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, feature_id)
                self.item_list.addItem(item)
            self.item_label.show()
            self.item_list.show()
        else:
            self.item_label.hide()
            self.item_list.hide()

        self.item_list.blockSignals(False)

    def update_visualization_buttons(self):
        selections = self.get_current_selections()
        recordings_selected = len(selections['recordings']) > 0
        analysis_level_selected = selections['analysis_level'] in ['recording', 'word', 'phoneme']
        items_selected = True

        if selections['analysis_level'] != 'recording':
            items_selected = len(selections['items']) > 0

        features_selected_count = len(selections['features'])

        # Timeline visualization
        time_line_enabled = recordings_selected and analysis_level_selected and items_selected
        if len(selections['recordings']) > 1 or (
                selections['analysis_level'] != 'recording' and len(selections['items']) > 1):
            time_line_enabled = time_line_enabled and features_selected_count == 1
        else:
            time_line_enabled = time_line_enabled and features_selected_count >= 1

        # Radar chart visualization
        radar_enabled = recordings_selected and analysis_level_selected and items_selected and features_selected_count >= 1

        # Histogram visualization
        histogram_enabled = recordings_selected and analysis_level_selected and items_selected and features_selected_count == 1

        # Boxplot visualization
        boxplot_enabled = recordings_selected and analysis_level_selected and items_selected and features_selected_count == 1

        # Vowel Chart visualization
        vowel_chart_enabled = recordings_selected and analysis_level_selected and items_selected and features_selected_count >= 1

        # Set the buttons
        self.time_line_btn.setEnabled(time_line_enabled)
        self.radar_btn.setEnabled(radar_enabled)
        self.histogram_btn.setEnabled(histogram_enabled)
        self.boxplot_btn.setEnabled(boxplot_enabled)
        self.vowel_chart_btn.setEnabled(vowel_chart_enabled)

    def disable_visualization_buttons(self):
        self.vowel_chart_btn.setEnabled(False)
        self.time_line_btn.setEnabled(False)
        self.histogram_btn.setEnabled(False)
        self.boxplot_btn.setEnabled(False)
        self.radar_btn.setEnabled(False)

    def visualize_time_line(self):
        features = self.fetch_filtered_features()
        if not features:
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111)

        try:
            all_table_data = self.visualization.plot_time_series(ax, features)
            self.canvas.draw()

            if all_table_data is not None:
                self.create_table(all_table_data, self.raw_data_table)
        except ValueError as ve:
            QMessageBox.critical(self, 'Plotting Error', str(ve))

    def visualize_histogram(self):
        features = self.fetch_filtered_features()
        if not features:
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111)

        try:
            histogram_data = self.visualization.plot_histogram(ax, features)
            self.canvas.draw()

            if histogram_data is not None:
                self.create_table(histogram_data, self.raw_data_table)
        except ValueError as ve:
            QMessageBox.critical(self, 'Plotting Error', str(ve))
            print(f"Error while plotting histogram: {ve}")

    def visualize_boxplot(self):
        features = self.fetch_filtered_features()
        if not features:
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111)

        try:
            boxplot_data = self.visualization.plot_boxplot(ax, features)
            self.canvas.draw()

            if boxplot_data is not None:
                self.create_table(boxplot_data, self.raw_data_table)
        except ValueError as ve:
            QMessageBox.critical(self, 'Plotting Error', str(ve))
            print(f"Error while plotting boxplot: {ve}")

    def visualize_radar(self):
        features = self.fetch_filtered_features()
        if not features:
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111, polar=True)

        try:
            radar_df_original, radar_df_normalized = self.visualization.plot_radar_chart(ax, features)
            self.canvas.draw()

            if radar_df_original is not None:
                self.create_table(radar_df_original, self.raw_data_table)
            if radar_df_normalized is not None:
                self.create_table(radar_df_normalized, self.normalized_data_table)
        except ValueError as ve:
            QMessageBox.critical(self, 'Plotting Error', str(ve))

    def visualize_vowel_chart(self):
        features = self.fetch_filtered_features()
        if not features:
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return

        self.clear_visualisation()
        ax = self.canvas.figure.add_subplot(111)

        try:
            vowel_chart_data = self.visualization.plot_vowel_chart(ax, features)
            self.canvas.draw()

            if vowel_chart_data is not None:
                self.create_table(vowel_chart_data, self.raw_data_table)
        except ValueError as ve:
            QMessageBox.critical(self, 'Plotting Error', str(ve))

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
