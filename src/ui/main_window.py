from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QFileDialog,
    QVBoxLayout, QMessageBox, QRadioButton, QButtonGroup,
    QHBoxLayout, QSpinBox, QSplitter, QGroupBox, QListWidgetItem, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem

from src.ui.selection_box import SelectionBox
from src.ui.visualization import Visualization
from src.speech_importer import SpeechImporter
from src.visualization_data_exporter import VisualizationDataExporter
from src.similarity_analyzer import SimilarityAnalyzer
from src.ui.recording_manager_window import RecordingsManager
from src.ui.audio_widget import AudioWidget


class MainWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.visualization = Visualization()
        self.database = db
        self.speech_importer = SpeechImporter(db)
        self.similarity_analyzer = SimilarityAnalyzer()
        self.setWindowTitle("Speech Analysis Application")
        self.resize(1920, 1080)
        self.showMaximized()

        global_font = QFont("Arial", 12)
        self.setFont(global_font)
        self.current_data_df = None
        self.init_ui()
        self.load_existing_recordings()

    def init_ui(self):

        # Main Split Layout: Control Panel and Visualization Area
        main_split_layout = QSplitter(Qt.Horizontal, self)

        # Control Panel Section
        control_panel_widget = self.create_control_panel()
        main_split_layout.addWidget(control_panel_widget)

        # Visualization Section
        visualization_section = self.create_visualization_section()
        main_split_layout.addWidget(visualization_section)

        # Adjust stretch
        main_split_layout.setStretchFactor(0, 2)
        main_split_layout.setStretchFactor(1, 3)

        # Main Application Layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(main_split_layout)
        self.setLayout(main_layout)

    def create_control_panel(self):
        """Creates the control panel with all input options."""
        control_panel_widget = QWidget()
        control_panel_layout = QVBoxLayout(control_panel_widget)

        # Manage Recordings Button
        self.manage_recordings_btn = QPushButton("Manage Recordings", self)
        self.manage_recordings_btn.clicked.connect(self.open_recordings_manager)
        control_panel_layout.addWidget(self.manage_recordings_btn)

        # Action Selection Group
        self.action_selection_group = self.create_action_selection()
        control_panel_layout.addWidget(self.action_selection_group)

        # Recording Selection
        self.recording_select_box = self.create_recording_selection()
        self.recording_select_box.selection_changed.connect(self.on_recording_select_changed)
        control_panel_layout.addWidget(self.recording_select_box)

        # Visualization Action Controls
        self.visualize_action_controls = self.create_visualize_action_controls()
        control_panel_layout.addWidget(self.visualize_action_controls)

        # Analysis Action Controls
        self.analyze_action_controls = self.create_analyze_action_controls()
        control_panel_layout.addWidget(self.analyze_action_controls)
        self.analyze_action_controls.setVisible(False)

        control_panel_layout.addStretch()

        return control_panel_widget

    def create_action_selection(self):
        """Creates the action selection radio buttons."""
        action_group = QGroupBox("Select Action", self)
        action_layout = QHBoxLayout()

        self.visualize_radio = QRadioButton("Visualize Features", self)
        self.analyze_radio = QRadioButton("Analyze Similarity", self)
        self.visualize_radio.setChecked(True)

        self.action_button_group = QButtonGroup(self)
        self.action_button_group.addButton(self.visualize_radio)
        self.action_button_group.addButton(self.analyze_radio)
        self.action_button_group.buttonClicked.connect(self.on_action_selection_changed)

        action_layout.addWidget(self.visualize_radio)
        action_layout.addWidget(self.analyze_radio)

        action_group.setLayout(action_layout)
        return action_group

    def create_recording_selection(self):
        """Creates the Recording Selection section."""
        recording_select_box = SelectionBox("Select Recordings:", multi_selection=True, parent=self)
        return recording_select_box

    def create_visualize_action_controls(self):
        """Creates the controls for the 'Visualize' action."""
        visualize_controls = QWidget()
        visualize_layout = QVBoxLayout(visualize_controls)

        # Add analysis level selection
        self.analysis_level_controls = self.create_analysis_level_selection()
        visualize_layout.addWidget(self.analysis_level_controls)

        # Add item selection
        self.item_selection_box = self.create_item_selection()
        visualize_layout.addWidget(self.item_selection_box)

        # Add feature selection
        self.feature_selection_box = self.create_feature_selection()
        visualize_layout.addWidget(self.feature_selection_box)

        # Add visualization type selection
        self.visualization_type_controls = self.create_visualization_type_selection()
        visualize_layout.addWidget(self.visualization_type_controls)

        # Add visualize/export buttons
        visualize_layout.addLayout(self.create_visualize_export_buttons())

        return visualize_controls

    def on_action_selection_changed(self):
        """Handle changes in the 'Select Action' radio buttons."""
        if self.visualize_radio.isChecked():
            self.visualize_action_controls.setVisible(True)
            self.analyze_action_controls.setVisible(False)
            self.clear_visualisation()

        elif self.analyze_radio.isChecked():
            self.visualize_action_controls.setVisible(False)
            self.analyze_action_controls.setVisible(True)
            self.clear_visualisation()
            self.analyze_btn.setEnabled(False)

    def create_analysis_level_selection(self):
        """Creates the Analysis Level Selection section."""
        analysis_level_group = QGroupBox("Select Analysis Level", self)
        analysis_level_layout = QHBoxLayout()
        self.recording_radio = QRadioButton("Recording")
        self.word_radio = QRadioButton("Word")
        self.phoneme_radio = QRadioButton("Phoneme")
        self.recording_radio.setChecked(True)
        self.analysis_level_group = QButtonGroup(self)
        self.analysis_level_group.addButton(self.recording_radio)
        self.analysis_level_group.addButton(self.word_radio)
        self.analysis_level_group.addButton(self.phoneme_radio)
        self.analysis_level_group.buttonClicked.connect(self.on_analysis_level_changed)
        analysis_level_layout.addWidget(self.recording_radio)
        analysis_level_layout.addWidget(self.word_radio)
        analysis_level_layout.addWidget(self.phoneme_radio)
        analysis_level_group.setLayout(analysis_level_layout)
        return analysis_level_group

    def create_item_selection(self):
        """Creates the Item Selection section."""
        item_selection_box = SelectionBox("Select Specific Words/Phonemes:", multi_selection=True, parent=self)
        item_selection_box.setVisible(False)
        item_selection_box.selection_changed.connect(self.on_items_changed)
        return item_selection_box

    def create_feature_selection(self):
        """Creates the Feature Selection section."""
        feature_selection_box = SelectionBox("Select Acoustic Features:", multi_selection=True, parent=self)
        feature_selection_box.selection_changed.connect(self.on_features_changed)
        return feature_selection_box

    def create_visualization_type_selection(self):
        """Creates the Visualization Type Selection section."""
        visualization_type_group = QGroupBox("Select Visualization Type", self)
        visualization_type_layout = QGridLayout()
        self.time_line_radio = QRadioButton("Timeline")
        self.histogram_radio = QRadioButton("Histogram")
        self.boxplot_radio = QRadioButton("Boxplot")
        self.radar_radio = QRadioButton("Radar Chart")
        self.vowel_chart_radio = QRadioButton("Vowel Chart")
        self.visualization_type_group = QButtonGroup(self)
        for rb in (self.time_line_radio, self.histogram_radio, self.boxplot_radio,
                   self.radar_radio, self.vowel_chart_radio):
            self.visualization_type_group.addButton(rb)
        self.time_line_radio.setChecked(True)
        self.visualization_type_group.buttonClicked.connect(self.on_viz_type_changed)

        self.viz_type = 'time_line'
        visualization_type_layout.addWidget(self.time_line_radio, 0, 0)
        visualization_type_layout.addWidget(self.histogram_radio, 0, 1)
        visualization_type_layout.addWidget(self.boxplot_radio, 1, 0)
        visualization_type_layout.addWidget(self.radar_radio, 1, 1)
        visualization_type_layout.addWidget(self.vowel_chart_radio, 2, 0)
        visualization_type_group.setLayout(visualization_type_layout)
        return visualization_type_group

    def create_visualize_export_buttons(self):
        """Creates the Visualize and Export buttons."""
        button_layout = QHBoxLayout()
        self.visualize_btn = QPushButton("Visualize", self)
        self.visualize_btn.clicked.connect(self.visualize_selected)
        button_layout.addWidget(self.visualize_btn)
        self.export_btn = QPushButton("Export Graph Data (JSON)", self)
        self.export_btn.clicked.connect(self.export_visualization_data_as_json)
        self.export_btn.setVisible(False)
        button_layout.addWidget(self.export_btn)
        return button_layout

    def create_analyze_action_controls(self):
        """Creates the Analysis Controls section."""
        analysis_widget = QWidget(self)
        analysis_layout = QVBoxLayout(analysis_widget)

        # Target Recording Selection
        self.target_recording_selection = SelectionBox("Select Target Recording:", multi_selection=False, parent=self)
        self.target_recording_selection.selection_changed.connect(self.on_target_recording_changed)
        analysis_layout.addWidget(self.target_recording_selection)

        # Number of Similar Items
        num_similar_group = QWidget(self)
        num_similar_layout = QVBoxLayout(num_similar_group)
        self.num_similar_label = QLabel("Number of similar items:", self)
        self.num_similar_spinbox = QSpinBox(self)
        self.num_similar_spinbox.setRange(1, 100)
        self.num_similar_spinbox.setValue(5)
        num_similar_layout.addWidget(self.num_similar_label)
        num_similar_layout.addWidget(self.num_similar_spinbox)
        analysis_layout.addWidget(num_similar_group)

        # Visualization Method
        visualization_method_group = QWidget(self)
        visualization_method_layout = QVBoxLayout(visualization_method_group)
        self.cluster_radio = QRadioButton("Cluster Analysis (PCA + KMeans)")
        self.feature_score_radio = QRadioButton("Feature Similarity Bars")
        self.pca_based_radio = QRadioButton("PCA-Based Similarity Bars")
        self.cluster_radio.setChecked(True)
        self.analysis_visualization_group = QButtonGroup(self)
        for rb in (self.cluster_radio, self.feature_score_radio, self.pca_based_radio):
            self.analysis_visualization_group.addButton(rb)
            visualization_method_layout.addWidget(rb)
        analysis_layout.addWidget(visualization_method_group)

        # Analyze Button
        self.analyze_btn = QPushButton("Analyze Similarity", self)
        self.analyze_btn.clicked.connect(self.analyze_similarity)
        self.analyze_btn.setEnabled(False)
        analysis_layout.addWidget(self.analyze_btn)

        return analysis_widget

    def create_visualization_section(self):
        visualization_splitter = QSplitter(Qt.Vertical)

        audio_widget_group = QGroupBox("Play Recordings")
        audio_widget_layout = QVBoxLayout(audio_widget_group)
        self.audio_widget = AudioWidget()
        self.audio_widget.setMinimumHeight(150)
        audio_widget_layout.addWidget(self.audio_widget)
        visualization_splitter.addWidget(audio_widget_group)

        feature_visualization_group = QGroupBox("Feature Visualization")
        feature_visualization_layout = QVBoxLayout(feature_visualization_group)
        self.plot_view = QWebEngineView(self)
        self.plot_view.setMinimumHeight(300)

        self.plot_view.page().profile().downloadRequested.connect(self.handle_download)

        feature_visualization_layout.addWidget(self.plot_view)
        visualization_splitter.addWidget(feature_visualization_group)

        table_view_group = QGroupBox("Table View")
        table_view_layout = QVBoxLayout(table_view_group)
        self.table_view = QWebEngineView(self)
        self.table_view.setMinimumHeight(120)
        table_view_layout.addWidget(self.table_view)
        visualization_splitter.addWidget(table_view_group)

        # Adjust splitter stretch factors
        visualization_splitter.setStretchFactor(0, 1)  # Audio Widget
        visualization_splitter.setStretchFactor(1, 8)  # Feature Visualization
        visualization_splitter.setStretchFactor(2, 1)  # Table View

        return visualization_splitter

    def open_recordings_manager(self):
        self.recording_manager_window = RecordingsManager(self.database, self)
        self.recording_manager_window.recordings_updated.connect(self.load_existing_recordings)
        self.recording_manager_window.exec_()

    def load_existing_recordings(self):
        """Load the recordings from the database into the selection boxes."""
        try:
            recordings = self.database.get_all_recordings()

            self.recording_select_box.clear_items()
            self.recording_select_box.add_items(recordings)

            self.target_recording_selection.clear_items()
            self.target_recording_selection.add_items(recordings)

            self.audio_widget.update_recording_list(recordings)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to load recordings from database: {str(e)}")

    def on_recording_select_changed(self):
        """Slot called when the user changes the selection of 'recording_select_box'."""
        self.update_feature_list()
        self.update_item_list()
        self.update_visualization_buttons()

    def on_analysis_level_changed(self):
        """Handle changes in the Analysis Level radio buttons."""
        level = self.get_selected_analysis_level()
        if level == 'recording':
            self.item_selection_box.setVisible(False)
        else:
            self.item_selection_box.setVisible(True)

        self.update_feature_list()
        self.update_item_list()
        self.update_visualization_buttons()
        self.clear_visualisation()

    def on_items_changed(self):
        """Handle changes in the Item Selection."""
        self.update_feature_list()
        self.update_visualization_buttons()
        self.clear_visualisation()

    def on_features_changed(self):
        """Handle changes in the Feature Selection."""
        self.update_visualization_buttons()
        self.clear_visualisation()

    def on_viz_type_changed(self):
        """Determine which radio button was clicked for Visualization Type."""
        btn = self.visualization_type_group.checkedButton()
        if not btn:
            return
        text = btn.text()
        if text == "Timeline":
            self.viz_type = 'time_line'
        elif text == "Histogram":
            self.viz_type = 'histogram'
        elif text == "Boxplot":
            self.viz_type = 'boxplot'
        elif text == "Radar Chart":
            self.viz_type = 'radar'
        elif text == "Vowel Chart":
            self.viz_type = 'vowel_chart'
        self.update_visualization_buttons()

    def get_selected_analysis_level(self):
        """Retrieve the selected analysis level."""
        if self.recording_radio.isChecked():
            return 'recording'
        elif self.phoneme_radio.isChecked():
            return 'phoneme'
        elif self.word_radio.isChecked():
            return 'word'

    def on_target_recording_changed(self):
        """Enable the Analyze button if a target recording is selected."""
        selected = len(self.target_recording_selection.get_selected_items()) > 0
        self.analyze_btn.setEnabled(selected)

    def get_current_selections(self):
        """
        Gather the user selections from the selection boxes:
          - recording_select_box
          - item_select_box
          - feature_select_box
        """
        analysis_level = self.get_selected_analysis_level()
        selected_recordings = self.recording_select_box.get_selected_items()

        selected_items = []
        if analysis_level != 'recording':
            selected_items = [
                it.data(Qt.UserRole) if it.data(Qt.UserRole) else it.text()
                for it in self.item_selection_box.list_widget.selectedItems()
            ]

        selected_features = self.feature_selection_box.get_selected_items()
        return {
            'recordings': selected_recordings,
            'analysis_level': analysis_level,
            'items': selected_items,
            'features': selected_features
        }

    def fetch_filtered_features(self):
        """Retrieve and filter features from the DB based on current selections."""
        selections = self.get_current_selections()
        selected_recordings = selections['recordings']
        analysis_level = selections['analysis_level']
        selected_items = selections['items']
        selected_features = selections['features']

        if not selected_recordings and self.viz_type != 'vowel_chart':
            return {}

        try:
            all_features = self.database.get_features_for_recordings(selected_recordings, analysis_level)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to fetch features: {str(e)}")
            return {}

        # Filter items if word/phoneme
        if analysis_level != 'recording' and selected_items:
            filtered_all = {}
            for rec_id, feats in all_features.items():
                filtered_feats = [f for f in feats if f.get("_id") in selected_items]
                if filtered_feats:
                    filtered_all[rec_id] = filtered_feats
            all_features = filtered_all

        # Filter features if needed
        if selected_features:
            filtered = {}
            for rec_id, feats in all_features.items():
                filtered_feats = []
                for feat in feats:
                    mean_filtered = {k: v for k, v in feat.get("mean", {}).items() if k in selected_features}
                    feature_names = list(feat.get("mean", {}).keys())
                    feature_indices = [i for i, k in enumerate(feature_names) if k in selected_features]

                    frame_values_filtered = []
                    for timestamp, values in feat.get("frame_values", []):
                        if values and feature_indices:
                            chosen_vals = [values[i] for i in feature_indices]
                            frame_values_filtered.append((timestamp, chosen_vals))
                        else:
                            frame_values_filtered.append((timestamp, []))

                    filtered_feat = {
                        "_id": feat.get("_id", ""),
                        "start": feat.get("start", ""),
                        "end": feat.get("end", ""),
                        "text": feat.get("text", ""),
                        "word_text": feat.get("word_text", ""),
                        "mean": mean_filtered,
                        "frame_values": frame_values_filtered
                    }
                    filtered_feats.append(filtered_feat)
                if filtered_feats:
                    filtered[rec_id] = filtered_feats
            all_features = filtered

        return all_features

    def update_feature_list(self):
        selections = self.get_current_selections()
        analysis_level = selections['analysis_level']
        selected_recordings = selections['recordings']
        selected_items = selections['items']

        self.feature_selection_box.list_widget.blockSignals(True)
        self.feature_selection_box.clear_items()
        self.feature_selection_box.list_widget.clearSelection()

        if not selected_recordings:
            self.feature_selection_box.list_widget.setEnabled(False)
            self.feature_selection_box.list_widget.blockSignals(False)
            return

        try:
            features = self.database.get_features_for_recordings(selected_recordings, analysis_level)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to fetch features: {str(e)}")
            self.feature_selection_box.list_widget.setEnabled(False)
            self.feature_selection_box.list_widget.blockSignals(False)
            return

        if not features:
            self.feature_selection_box.list_widget.setEnabled(False)
            self.feature_selection_box.list_widget.blockSignals(False)
            return

        all_features = set()
        if analysis_level != 'recording' and selected_items:
            for feat_list in features.values():
                for feat in feat_list:
                    if feat.get("_id") in selected_items:
                        all_features.update(feat.get("mean", {}).keys())
        else:
            for feat_list in features.values():
                for feat in feat_list:
                    all_features.update(feat.get("mean", {}).keys())

        if all_features:
            sorted_features = sorted(all_features)
            self.feature_selection_box.add_items(sorted_features)
            self.feature_selection_box.list_widget.setEnabled(True)
        else:
            self.feature_selection_box.list_widget.setEnabled(False)

        self.feature_selection_box.list_widget.blockSignals(False)

    def update_item_list(self):
        level = self.get_selected_analysis_level()
        selected_recordings = self.recording_select_box.get_selected_items()

        self.item_selection_box.list_widget.blockSignals(True)
        self.item_selection_box.clear_items()
        self.item_selection_box.list_widget.clearSelection()

        if level == 'recording' or not selected_recordings:
            self.item_selection_box.setVisible(False)
            self.item_selection_box.list_widget.hide()
            self.item_selection_box.list_widget.blockSignals(False)
            return

        try:
            features = self.database.get_features_for_recordings(selected_recordings, level)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to fetch features: {str(e)}")
            self.item_selection_box.setVisible(False)
            self.item_selection_box.list_widget.hide()
            self.item_selection_box.list_widget.blockSignals(False)
            return

        if not features:
            self.item_selection_box.setVisible(False)
            self.item_selection_box.list_widget.hide()
            self.item_selection_box.list_widget.blockSignals(False)
            return

        word_counters = {}
        phoneme_counters = {}

        items_by_recording = []
        for rec_id, feat_list in features.items():
            rec_items = []
            for feat in feat_list:
                item_text = feat.get('text', '').strip()
                fid = feat.get('_id')
                word_text = feat.get('word_text', '')

                frame_vals = feat.get('frame_values', [])
                if not frame_vals:
                    continue

                timestamp = frame_vals[0][0] if frame_vals else None
                if not item_text or timestamp is None:
                    continue

                if level == 'word':
                    word_counters[rec_id] = word_counters.get(rec_id, 0) + 1
                    w_num = word_counters[rec_id]
                    unique_label = f"{rec_id}: {item_text} (#{w_num})"

                elif level == 'phoneme':
                    key = (rec_id, word_text)
                    phoneme_counters[key] = phoneme_counters.get(key, 0) + 1
                    p_num = phoneme_counters[key]
                    unique_label = (
                        f"{rec_id}: {word_text} - {item_text} (#{p_num})"
                    )

                rec_items.append((timestamp, unique_label, fid))

            rec_items.sort(key=lambda x: x[0])
            items_by_recording.extend(rec_items)

        if items_by_recording:
            for _, it_text, fid in items_by_recording:
                list_item = QListWidgetItem(it_text)
                list_item.setData(Qt.UserRole, fid)
                self.item_selection_box.list_widget.addItem(list_item)
            self.item_selection_box.setVisible(True)
            self.item_selection_box.list_widget.show()
        else:
            self.item_selection_box.setVisible(False)
            self.item_selection_box.list_widget.hide()

        self.item_selection_box.list_widget.blockSignals(False)

    def update_visualization_buttons(self):
        selections = self.get_current_selections()
        level = selections['analysis_level']
        selected_viz = self.viz_type
        num_features = len(selections['features'])

        can_visualize = False

        if selected_viz in ['time_line', 'histogram', 'boxplot']:
            if level == 'recording':
                rec_count = len(selections['recordings'])
                if (rec_count > 1 and num_features == 1) or (rec_count == 1 and num_features >= 1):
                    can_visualize = True
            else:
                item_count = len(selections['items'])
                if (item_count > 1 and num_features == 1) or (item_count == 1 and num_features >= 1):
                    can_visualize = True
        elif selected_viz == 'radar':
            if len(selections['recordings']) > 0 and level in ['recording', 'word', 'phoneme'] and num_features > 0:
                can_visualize = True
        elif selected_viz == 'vowel_chart':
            if len(selections['recordings']) > 0 and level in ['recording', 'word', 'phoneme']:
                can_visualize = True

        self.visualize_btn.setEnabled(can_visualize)

    def visualize_selected(self):
        if not self.viz_type:
            QMessageBox.warning(self, 'Error', "Please select a visualization type.")
            return

        features = self.fetch_filtered_features()
        if not features and self.viz_type != 'vowel_chart':
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return

        if self.viz_type == 'time_line':
            self.visualize_time_line()
        elif self.viz_type == 'histogram':
            self.visualize_histogram()
        elif self.viz_type == 'boxplot':
            self.visualize_boxplot()
        elif self.viz_type == 'radar':
            self.visualize_radar()
        elif self.viz_type == 'vowel_chart':
            self.visualize_vowel_chart()

    def display_figure(self, fig, data_df=None):
        config = {
            'modeBarButtons': [
                ['zoomIn2d', 'zoomOut2d', 'pan2d', 'autoScale2d', 'toImage']
            ],
            'displayModeBar': True,
            'displaylogo': False
        }
        html = fig.to_html(include_plotlyjs='cdn', config=config)
        self.plot_view.setHtml(html)

        if data_df is not None and not data_df.empty:
            self.current_data_df = data_df.copy()
            table_html = self.visualization.create_plotly_table(data_df)
            self.table_view.setHtml(table_html)

        self.export_btn.setVisible(True)

    def visualize_time_line(self):
        features = self.fetch_filtered_features()
        if not features:
            return
        try:
            analysis_level = self.get_selected_analysis_level()
            fig, table_data = self.visualization.plot_time_series(features, analysis_level)
            self.display_figure(fig, table_data)
        except ValueError as ve:
            QMessageBox.critical(self, 'Plotting Error', str(ve))

    def visualize_histogram(self):
        features = self.fetch_filtered_features()
        if not features:
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return
        try:
            fig, histogram_data = self.visualization.plot_histogram(features)
            self.display_figure(fig, histogram_data)
        except ValueError as ve:
            QMessageBox.critical(self, 'Plotting Error', str(ve))

    def visualize_boxplot(self):
        features = self.fetch_filtered_features()
        if not features:
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return
        try:
            fig, boxplot_data = self.visualization.plot_boxplot(features)
            self.display_figure(fig, boxplot_data)
        except ValueError as ve:
            QMessageBox.critical(self, 'Plotting Error', str(ve))

    def visualize_radar(self):
        features = self.fetch_filtered_features()
        if not features:
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return
        try:
            fig, radar_df = self.visualization.plot_radar_chart(features)
            self.display_figure(fig, radar_df)
        except ValueError as ve:
            QMessageBox.critical(self, 'Plotting Error', str(ve))

    def visualize_vowel_chart(self):
        selections = self.get_current_selections()
        level = selections['analysis_level']
        recs = selections['recordings']
        items = selections['items']

        try:
            if level == 'phoneme':
                vowel_data = self.database.get_vowels(items, "_id")
            elif level == 'word':
                vowel_data = self.database.get_vowels(items, "parent_id")
            elif level == 'recording':
                vowel_data = self.database.get_vowels(recs, "recording_id")
            else:
                QMessageBox.warning(self, 'Error', "Invalid analysis level selected.")
                return
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to fetch vowel data: {str(e)}")
            return

        flat_data = []
        for _, phoneme_list in vowel_data.items():
            for p in phoneme_list:
                if "F1" in p and "F2" in p:
                    flat_data.append({
                        "F1": p["F1"],
                        "F2": p["F2"],
                        "Vowel": p["Phoneme"],
                        "Recording": p.get("Recording"),
                        "Word": p.get("Word")
                    })

        if not flat_data:
            QMessageBox.information(self, 'No Vowels', "No vowel data found for the selected selections.")
            return

        try:
            fig, df = self.visualization.plot_vowel_chart(flat_data)
            self.display_figure(fig, df)
        except ValueError as ve:
            QMessageBox.critical(self, 'Plotting Error', str(ve))

    def analyze_similarity(self):
        target_items = self.target_recording_selection.get_selected_items()
        selections = self.get_current_selections()
        selected_recs = selections["recordings"]

        if not target_items:
            QMessageBox.warning(self, "Error", "Please select a target recording.")
            return
        target_rec = target_items[0]

        features = self.database.get_mean_features(selected_recs)
        if not features:
            QMessageBox.warning(self, "Error", "No features available for similarity.")
            return

        df = self.similarity_analyzer.prepare_feature_matrix(features)
        if df.empty:
            QMessageBox.warning(self, "Error", "No valid features found for similarity.")
            return

        top_n = self.num_similar_spinbox.value()

        if self.cluster_radio.isChecked():
            try:
                (X_pca_vis, labels, rec_ids, target_rec_id,
                 similar_list, cos_sims, cos_dists) = self.similarity_analyzer.analyze_clusters(
                    target_rec, df, top_n
                )
                fig, cluster_df = self.visualization.plot_clusters_with_distances(
                    X_pca_vis, labels, rec_ids, target_rec_id, similar_list, cos_sims, cos_dists
                )
                self.display_figure(fig, cluster_df)
            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))

        elif self.feature_score_radio.isChecked():
            try:
                target_rec_id, similar_list = self.similarity_analyzer.analyze_scores(
                    target_rec, df, top_n, method='cosine'
                )
                fig, sim_df = self.visualization.plot_similarity_bars(
                    target_rec_id, similar_list, measure_name="Feature Cosine Similarity"
                )
                self.display_figure(fig, sim_df)
            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))

        elif self.pca_based_radio.isChecked():
            try:
                target_rec_id, distance_list = self.similarity_analyzer.analyze_scores(
                    target_rec, df, top_n, method='pca_cosine_distance'
                )
                similarity_list = [(r, 1 - d) for (r, d) in distance_list]
                similarity_list.sort(key=lambda x: x[1], reverse=True)
                fig, sim_df = self.visualization.plot_similarity_bars(
                    target_rec_id, similarity_list, measure_name="PCA Cosine Similarity"
                )
                self.display_figure(fig, sim_df)
            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))

    def clear_visualisation(self):
        self.plot_view.setHtml("<html><body></body></html>")
        self.table_view.setHtml("<html><body></body></html>")
        self.current_data_df = None

        self.export_btn.setVisible(False)

    def handle_download(self, download_item: QWebEngineDownloadItem):
        """
        Called when the user tries to download.
        """
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Snapshot",
            download_item.suggestedFileName(),
            "Images (*.png)"
        )
        if save_path:
            download_item.setPath(save_path)
            download_item.accept()
            QMessageBox.information(self, "Download Started", f"Saving to {save_path}")
        else:
            download_item.cancel()

    def export_visualization_data_as_json(self):
        """
        Export the current DataFrame as JSON.
        """
        if self.current_data_df is not None and not self.current_data_df.empty:
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Graph Data (JSON)",
                "graph_data.json",
                "JSON Files (*.json)"
            )
            if save_path:
                try:
                    import json
                    data_records = self.current_data_df.to_dict(orient="records")
                    with open(save_path, "w", encoding="utf-8") as f:
                        json.dump(data_records, f, ensure_ascii=False, indent=2)
                    QMessageBox.information(self, "Export Complete", f"JSON saved to {save_path}")
                except Exception as ex:
                    QMessageBox.critical(self, "Export Error", f"Failed to export JSON:\n{str(ex)}")
        else:
            QMessageBox.information(self, "No data to export", "No current DataFrame to export.")
