from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QFileDialog, QVBoxLayout,
    QMessageBox, QListWidget, QAbstractItemView, QSplitter,
    QTableWidget, QTableWidgetItem, QRadioButton, QButtonGroup, QListWidgetItem, QHBoxLayout,
    QGroupBox, QSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem
from src.ui.visualization import Visualization
from src.speech_importer import SpeechImporter
from src.visualization_data_exporter import VisualizationDataExporter
from src.similarity_analyzer import SimilarityAnalyzer

class MainWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.visualization = Visualization()
        self.database = db
        self.speech_importer = SpeechImporter(db)
        self.init_ui()
        self.load_existing_recordings()
        self.similarity_analyzer = SimilarityAnalyzer()

    def init_ui(self):
        self.setWindowTitle("Speech Analysis Application")
        main_splitter = QSplitter(Qt.Horizontal)

        # Control Panel
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)

        # Import section
        self.label = QLabel("Upload audio and TextGrid files:", self)
        self.label.setAlignment(Qt.AlignCenter)

        self.upload_btn = QPushButton("Import Files", self)
        self.upload_btn.clicked.connect(self.upload_files)

        control_layout.addWidget(self.label)
        control_layout.addWidget(self.upload_btn)

        # Action selection
        action_group_box = QGroupBox("Select Action", self)
        action_layout = QHBoxLayout()

        self.visualize_radio = QRadioButton("Visualize")
        self.analyze_radio = QRadioButton("Analyze Similarity")
        self.visualize_radio.setChecked(True)

        self.action_group = QButtonGroup(self)
        self.action_group.addButton(self.visualize_radio)
        self.action_group.addButton(self.analyze_radio)
        self.action_group.buttonClicked.connect(self.on_action_selection_changed)

        action_layout.addWidget(self.visualize_radio)
        action_layout.addWidget(self.analyze_radio)
        action_group_box.setLayout(action_layout)

        control_layout.addWidget(action_group_box)

        # Available recordings
        control_layout.addWidget(QLabel("Available Recordings:", self))
        self.file_list_widget = QListWidget(self)
        self.file_list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.file_list_widget.itemSelectionChanged.connect(self.on_recordings_changed)
        control_layout.addWidget(self.file_list_widget)

        # Visualization controls
        self.visualization_controls = QGroupBox("Visualization Controls", self)
        viz_layout = QVBoxLayout()

        # Analysis level selection
        self.analysis_label = QLabel("Select Analysis Level:", self)
        self.analysis_label.setAlignment(Qt.AlignCenter)

        self.recording_radio = QRadioButton("Recording")
        self.word_radio = QRadioButton("Word")
        self.phoneme_radio = QRadioButton("Phoneme")
        self.recording_radio.setChecked(True)

        self.analysis_group = QButtonGroup(self)
        self.analysis_group.addButton(self.recording_radio)
        self.analysis_group.addButton(self.word_radio)
        self.analysis_group.addButton(self.phoneme_radio)
        self.analysis_group.buttonClicked.connect(self.on_analysis_level_changed)

        viz_layout.addWidget(self.analysis_label)
        viz_layout.addWidget(self.recording_radio)
        viz_layout.addWidget(self.word_radio)
        viz_layout.addWidget(self.phoneme_radio)

        # Available items
        self.item_group_box = QGroupBox("Available Items", self)
        item_layout = QVBoxLayout()

        self.item_label = QLabel("Available Words/Phonemes:", self)
        self.item_label.setAlignment(Qt.AlignCenter)
        self.item_label.setVisible(False)

        self.item_list = QListWidget(self)
        self.item_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.item_list.setVisible(False)
        self.item_list.itemSelectionChanged.connect(self.on_items_changed)

        item_layout.addWidget(self.item_label)
        item_layout.addWidget(self.item_list)
        self.item_group_box.setLayout(item_layout)
        self.item_group_box.setVisible(False)

        viz_layout.addWidget(self.item_group_box)

        # Available features
        self.feature_label = QLabel("Available Features:", self)
        self.feature_label.setAlignment(Qt.AlignCenter)

        self.feature_list = QListWidget(self)
        self.feature_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.feature_list.itemSelectionChanged.connect(self.on_features_changed)

        viz_layout.addWidget(self.feature_label)
        viz_layout.addWidget(self.feature_list)

        # Visualization type
        self.visualization_type_label = QLabel("Select Visualization Type:", self)
        self.visualization_type_label.setAlignment(Qt.AlignCenter)

        self.viz_radio_group = QButtonGroup(self)
        self.time_line_radio = QRadioButton("Timeline")
        self.histogram_radio = QRadioButton("Histogram")
        self.boxplot_radio = QRadioButton("Boxplot")
        self.radar_radio = QRadioButton("Radar Chart")
        self.vowel_chart_radio = QRadioButton("Vowel Chart")
        self.time_line_radio.setChecked(True)
        self.viz_type = 'time_line'

        self.viz_radio_group.buttonClicked.connect(self.on_viz_type_changed)

        self.viz_radio_group.addButton(self.time_line_radio)
        self.viz_radio_group.addButton(self.histogram_radio)
        self.viz_radio_group.addButton(self.boxplot_radio)
        self.viz_radio_group.addButton(self.radar_radio)
        self.viz_radio_group.addButton(self.vowel_chart_radio)

        viz_layout.addWidget(self.visualization_type_label)
        viz_layout.addWidget(self.time_line_radio)
        viz_layout.addWidget(self.histogram_radio)
        viz_layout.addWidget(self.boxplot_radio)
        viz_layout.addWidget(self.radar_radio)
        viz_layout.addWidget(self.vowel_chart_radio)

        # Visualize/export buttons
        viz_buttons_layout = QHBoxLayout()
        self.visualize_btn = QPushButton("Visualize", self)
        self.visualize_btn.clicked.connect(self.visualize_selected)

        self.export_menu_button = QPushButton("Export JSON", self)
        self.export_menu_button.clicked.connect(self.export_visualization_data_as_json)
        self.export_menu_button.setVisible(False)

        viz_buttons_layout.addWidget(self.visualize_btn)
        viz_buttons_layout.addWidget(self.export_menu_button)

        viz_layout.addLayout(viz_buttons_layout)

        self.visualization_controls.setLayout(viz_layout)
        control_layout.addWidget(self.visualization_controls)

        # Analysis control
        self.analysis_controls = QGroupBox("Analyze Similarity", self)
        analysis_layout = QVBoxLayout()

        # Select target recording
        target_recording_group_box = QGroupBox("Select Target Recording", self)
        target_layout = QVBoxLayout()
        self.target_recording_list = QListWidget(self)
        self.target_recording_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.target_recording_list.itemSelectionChanged.connect(self.on_target_recording_changed)

        target_layout.addWidget(self.target_recording_list)
        target_recording_group_box.setLayout(target_layout)
        analysis_layout.addWidget(target_recording_group_box)

        # Number of similar recordings
        num_similar_group_box = QGroupBox("Number of Similar Recordings", self)
        num_similar_layout = QHBoxLayout()
        self.num_similar_label = QLabel("N:", self)
        self.num_similar_spinbox = QSpinBox(self)
        self.num_similar_spinbox.setMinimum(1)
        self.num_similar_spinbox.setMaximum(100)
        self.num_similar_spinbox.setValue(5)

        num_similar_layout.addWidget(self.num_similar_label)
        num_similar_layout.addWidget(self.num_similar_spinbox)
        num_similar_group_box.setLayout(num_similar_layout)
        analysis_layout.addWidget(num_similar_group_box)

        # Analysis: Select visualisation
        visualization_method_box = QGroupBox("Select Visualization", self)
        visualization_method_layout = QVBoxLayout()

        self.cluster_radio = QRadioButton("Features (PCA) Cosine Similarity with Clusters (KNN)")
        self.original_feature_score_radio = QRadioButton("Features Cosine Similarity Bars")
        self.pca_based_radio = QRadioButton("Features (PCA) Cosine Similarity Bars")
        self.cluster_radio.setChecked(True)

        self.analysis_viz_group = QButtonGroup(self)
        self.analysis_viz_group.addButton(self.cluster_radio)
        self.analysis_viz_group.addButton(self.original_feature_score_radio)
        self.analysis_viz_group.addButton(self.pca_based_radio)

        visualization_method_layout.addWidget(self.cluster_radio)
        visualization_method_layout.addWidget(self.original_feature_score_radio)
        visualization_method_layout.addWidget(self.pca_based_radio)
        visualization_method_box.setLayout(visualization_method_layout)
        analysis_layout.addWidget(visualization_method_box)

        # Analyze button
        self.analyze_btn = QPushButton("Analyze", self)
        self.analyze_btn.clicked.connect(self.analyze_similarity)
        self.analyze_btn.setEnabled(False)
        analysis_layout.addWidget(self.analyze_btn)

        self.analysis_controls.setLayout(analysis_layout)
        self.analysis_controls.setVisible(False)
        control_layout.addWidget(self.analysis_controls)

        control_layout.addStretch()

        # Visualization and data tables
        vis_data_splitter = QSplitter(Qt.Vertical)

        # Visualization
        self.plot_view = QWebEngineView(self)
        self.plot_view.page().profile().downloadRequested.connect(self.handle_download)

        visualization_panel = QWidget()
        visualization_layout = QVBoxLayout(visualization_panel)
        visualization_layout.addWidget(self.plot_view)

        # Data tables
        self.raw_data_table = QTableWidget(self)
        self.normalized_data_table = QTableWidget(self)
        raw_data_label = QLabel("Original Data", self)
        normalized_data_label = QLabel("Normalized Data", self)
        data_tables_panel = QWidget()
        data_tables_layout = QHBoxLayout(data_tables_panel)

        raw_data_layout = QVBoxLayout()
        raw_data_layout.addWidget(raw_data_label)
        raw_data_layout.addWidget(self.raw_data_table)

        normalized_data_layout = QVBoxLayout()
        normalized_data_layout.addWidget(normalized_data_label)
        normalized_data_layout.addWidget(self.normalized_data_table)

        data_tables_layout.addLayout(raw_data_layout)
        data_tables_layout.addLayout(normalized_data_layout)

        vis_data_splitter.addWidget(visualization_panel)
        vis_data_splitter.addWidget(data_tables_panel)
        vis_data_splitter.setStretchFactor(0, 6)
        vis_data_splitter.setStretchFactor(1, 0)

        main_splitter.addWidget(control_panel)
        main_splitter.addWidget(vis_data_splitter)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 3)

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
        self.update_feature_list()
        self.update_item_list()
        self.update_visualization_buttons()
        self.clear_visualisation()

        selected_recordings = [item.text() for item in self.file_list_widget.selectedItems()]
        if self.analysis_controls.isVisible():
            self.target_recording_list.clear()
            self.target_recording_list.addItems(selected_recordings)

    def on_action_selection_changed(self):
        if self.visualize_radio.isChecked():
            self.visualization_controls.setVisible(True)
            self.analysis_controls.setVisible(False)
            self.clear_visualisation()
        elif self.analyze_radio.isChecked():
            self.visualization_controls.setVisible(False)
            self.analysis_controls.setVisible(True)
            self.clear_visualisation()
            self.analyze_btn.setEnabled(False)

    def on_analysis_level_changed(self):
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

    def on_viz_type_changed(self):
        if self.time_line_radio.isChecked():
            self.viz_type = 'time_line'
        elif self.histogram_radio.isChecked():
            self.viz_type = 'histogram'
        elif self.boxplot_radio.isChecked():
            self.viz_type = 'boxplot'
        elif self.radar_radio.isChecked():
            self.viz_type = 'radar'
        elif self.vowel_chart_radio.isChecked():
            self.viz_type = 'vowel_chart'

        self.update_visualization_buttons()

    def get_selected_analysis_level(self):
        if self.recording_radio.isChecked():
            return 'recording'
        elif self.phoneme_radio.isChecked():
            return 'phoneme'
        elif self.word_radio.isChecked():
            return 'word'

    def on_target_recording_changed(self):
        selected = len(self.target_recording_list.selectedItems()) > 0
        self.analyze_btn.setEnabled(selected)

    def get_current_selections(self):
        selected_recordings = [item.text() for item in self.file_list_widget.selectedItems()]
        analysis_level = self.get_selected_analysis_level()
        selected_items = [item.data(Qt.UserRole) for item in self.item_list.selectedItems()] if analysis_level != 'recording' else []
        selected_features = [item.text() for item in self.feature_list.selectedItems()]

        return {
            'recordings': selected_recordings,
            'analysis_level': analysis_level,
            'items': selected_items,
            'features': selected_features
        }

    def fetch_filtered_features(self):
        selections = self.get_current_selections()
        selected_recordings = selections['recordings']
        analysis_level = selections['analysis_level']

        if not selected_recordings and self.viz_type != 'vowel_chart':
            return {}

        # Fetch all features for selected recordings/analysis_level
        try:
            all_features = self.database.get_features_for_recordings(selected_recordings, analysis_level)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to fetch features: {str(e)}")
            return {}

        selected_items = selections['items']
        selected_features = selections['features']

        # Filter items if we are at word/phoneme level
        if analysis_level != 'recording' and selected_items:
            filtered_all_features = {}
            for rec_id, features in all_features.items():
                filtered_feats = [f for f in features if f.get("_id") in selected_items]
                if filtered_feats:
                    filtered_all_features[rec_id] = filtered_feats
            all_features = filtered_all_features

        # Filter features if specific features are selected
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
                            selected_vals = [values[i] for i in feature_indices]
                            frame_values_filtered.append((timestamp, selected_vals))
                        else:
                            frame_values_filtered.append((timestamp, []))

                    filtered_feat = {
                        "text": feat.get("text", ""),
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

        self.feature_list.blockSignals(True)
        self.feature_list.clear()
        self.feature_list.clearSelection()

        if not selected_recordings:
            self.feature_list.setEnabled(False)
            self.feature_list.blockSignals(False)
            return

        try:
            features = self.database.get_features_for_recordings(selected_recordings, analysis_level)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to fetch features: {str(e)}")
            self.feature_list.setEnabled(False)
            self.feature_list.blockSignals(False)
            return

        if not features:
            self.feature_list.setEnabled(False)
            self.feature_list.blockSignals(False)
            return

        # Filter by selected items if word/phoneme
        all_features = set()
        if analysis_level != 'recording' and selected_items:
            for rec_id, feat_list in features.items():
                for feat in feat_list:
                    if feat.get("_id") in selected_items:
                        all_features.update(feat.get("mean", {}).keys())
        else:
            for feat_list in features.values():
                for feat in feat_list:
                    all_features.update(feat.get("mean", {}).keys())

        if all_features:
            sorted_features = sorted(all_features)
            self.feature_list.addItems(sorted_features)
            self.feature_list.setEnabled(True)
        else:
            self.feature_list.setEnabled(False)

        self.feature_list.blockSignals(False)

    def update_item_list(self):
        analysis_level = self.get_selected_analysis_level()
        selected_recordings = [item.text() for item in self.file_list_widget.selectedItems()]

        self.item_list.blockSignals(True)
        self.item_list.clear()
        self.item_list.clearSelection()

        if analysis_level == 'recording' or not selected_recordings:
            self.item_group_box.setVisible(False)
            self.item_list.hide()
            self.item_label.hide()
            self.item_list.blockSignals(False)
            return

        try:
            features = self.database.get_features_for_recordings(selected_recordings, analysis_level)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to fetch features: {str(e)}")
            self.item_group_box.setVisible(False)
            self.item_list.hide()
            self.item_label.hide()
            self.item_list.blockSignals(False)
            return

        if not features:
            self.item_group_box.setVisible(False)
            self.item_list.hide()
            self.item_label.hide()
            self.item_list.blockSignals(False)
            return

        items_by_recording = []
        for rec_id, feat_list in features.items():
            rec_items = []
            for feat in feat_list:
                item_text = feat.get('text', '').strip()
                timestamp = feat.get('frame_values', [])[0][0] if feat.get('frame_values') else None
                if item_text and timestamp is not None:
                    feature_id = feat.get('_id')
                    rec_items.append((timestamp, f"{rec_id} - {item_text}", feature_id))
            rec_items = sorted(rec_items, key=lambda x: x[0])
            items_by_recording.extend(rec_items)

        if items_by_recording:
            for _, it_text, feat_id in items_by_recording:
                item = QListWidgetItem(it_text)
                item.setData(Qt.UserRole, feat_id)
                self.item_list.addItem(item)
            self.item_group_box.setVisible(True)
            self.item_label.show()
            self.item_list.show()
        else:
            self.item_group_box.setVisible(False)
            self.item_list.hide()
            self.item_label.hide()

        self.item_list.blockSignals(False)

    def update_visualization_buttons(self):
        selections = self.get_current_selections()
        analysis_level = selections['analysis_level']
        selected_viz = self.viz_type
        num_features = len(selections['features'])

        visualize_enabled = False

        if selected_viz in ['time_line', 'histogram', 'boxplot']:
            if analysis_level == 'recording':
                num_recordings = len(selections['recordings'])
                if (num_recordings > 1 and num_features == 1) or (num_recordings == 1 and num_features >= 1):
                    visualize_enabled = True
            else:
                num_items = len(selections['items'])
                if (num_items > 1 and num_features == 1) or (num_items == 1 and num_features >= 1):
                    visualize_enabled = True
        elif selected_viz == 'radar':
            if len(selections['recordings']) > 0 and analysis_level in ['recording', 'word', 'phoneme'] and num_features > 0:
                visualize_enabled = True
        elif selected_viz == 'vowel_chart':
            if len(selections['recordings']) > 0 and analysis_level in ['recording', 'word', 'phoneme']:
                visualize_enabled = True

        self.visualize_btn.setEnabled(visualize_enabled)

    def disable_visualization_buttons(self):
        self.visualize_btn.setEnabled(False)

    def visualize_selected(self):
        selected_viz = self.viz_type

        if not selected_viz:
            QMessageBox.warning(self, 'Error', "Please select a visualization type.")
            return

        features = self.fetch_filtered_features()
        if not features and selected_viz != 'vowel_chart':
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return

        if selected_viz == 'time_line':
            self.visualize_time_line()
        elif selected_viz == 'histogram':
            self.visualize_histogram()
        elif selected_viz == 'boxplot':
            self.visualize_boxplot()
        elif selected_viz == 'radar':
            self.visualize_radar()
        elif selected_viz == 'vowel_chart':
            self.visualize_vowel_chart()

    def visualize_time_line(self):
        features = self.fetch_filtered_features()
        if not features:
            return
        try:
            fig, all_table_data = self.visualization.plot_time_series(features)
            self.display_figure(fig, all_table_data)
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
            print(f"Error while plotting histogram: {ve}")

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
            print(f"Error while plotting boxplot: {ve}")

    def visualize_radar(self):
        features = self.fetch_filtered_features()
        if not features:
            QMessageBox.warning(self, 'Error', "Please select recordings and features to visualize.")
            return

        try:
            fig, (radar_df_original, radar_df_normalized) = self.visualization.plot_radar_chart(features)
            self.display_figure(fig, radar_df_original, radar_df_normalized)
        except ValueError as ve:
            QMessageBox.critical(self, 'Plotting Error', str(ve))

    def visualize_vowel_chart(self):
        selections = self.get_current_selections()
        analysis_level = selections['analysis_level']
        selected_recordings = selections['recordings']
        selected_items = selections['items']

        try:
            if analysis_level == 'phoneme':
                vowel_data = self.database.get_vowels(selected_items, "_id")
            elif analysis_level == 'word':
                vowel_data = self.database.get_vowels(selected_items, "parent_id")
            elif analysis_level == 'recording':
                vowel_data = self.database.get_vowels(selected_recordings, "recording_id")
            else:
                QMessageBox.warning(self, 'Error', "Invalid analysis level selected.")
                return
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"Failed to fetch vowel data: {str(e)}")
            return

        flat_vowel_data = []
        for _, phoneme_list in vowel_data.items():
            for phoneme in phoneme_list:
                if "F1" in phoneme and "F2" in phoneme:
                    flat_vowel_data.append({
                        "F1": phoneme["F1"],
                        "F2": phoneme["F2"],
                        "Vowel": phoneme["Phoneme"],
                        "Recording": phoneme.get("Recording"),
                        "Word": phoneme.get("Word")
                    })

        if not flat_vowel_data:
            QMessageBox.information(self, 'No Vowels', "No vowel data found for the selected selections.")
            return

        try:
            fig, (vowel_df_original, vowel_df_normalized) = self.visualization.plot_vowel_chart(flat_vowel_data)
            self.display_figure(fig, vowel_df_original, vowel_df_normalized)
        except ValueError as ve:
            QMessageBox.critical(self, 'Plotting Error', str(ve))

    def analyze_similarity(self):
        target_items = self.target_recording_list.selectedItems()
        selections = self.get_current_selections()
        selected = selections.get("recordings")

        if not target_items:
            QMessageBox.warning(self, "Error", "Please select a target recording.")
            return

        target_recording = target_items[0].text()
        features = self.database.get_mean_features(selected)

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
                (X_pca_vis, labels, recording_ids, target_rec, similar_list,
                 cos_sims, cos_dists) = self.similarity_analyzer.analyze_clusters(target_recording, df, top_n)
                fig, cluster_df = self.visualization.plot_clusters_with_distances(
                    X_pca_vis, labels, recording_ids, target_rec, similar_list, cos_sims, cos_dists
                )
                self.display_figure(fig, cluster_df)

            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))

        elif self.original_feature_score_radio.isChecked():
            try:
                target_rec, similar_list = self.similarity_analyzer.analyze_scores(
                    target_recording, df, top_n, method='cosine'
                )
                fig, sim_df = self.visualization.plot_similarity_bars(
                    target_rec, similar_list, measure_name="Original Feature Cosine Similarity"
                )
                self.display_figure(fig, sim_df)
            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))

        elif self.pca_based_radio.isChecked():
            try:
                target_rec, distance_list = self.similarity_analyzer.analyze_scores(
                    target_recording, df, top_n, method='pca_cosine_distance'
                )

                similarity_list = [(r, 1 - d) for r, d in distance_list]
                similarity_list.sort(key=lambda x: x[1], reverse=True)

                fig, sim_df = self.visualization.plot_similarity_bars(
                    target_rec, similarity_list, measure_name="PCA Cosine Similarity"
                )
                self.display_figure(fig, sim_df)
            except ValueError as ve:
                QMessageBox.warning(self, "Error", str(ve))

    def display_figure(self, fig, raw_df=None, norm_df=None):
        config = {
            'modeBarButtons': [
                ['zoomIn2d', 'zoomOut2d', 'pan2d', 'autoScale2d', 'toImage']
            ],
            'displayModeBar': True,
            'displaylogo': False
        }
        html = fig.to_html(include_plotlyjs='cdn', config=config)
        self.plot_view.setHtml(html)

        self.raw_data_table.clearContents()
        self.raw_data_table.setRowCount(0)
        self.raw_data_table.setColumnCount(0)
        self.normalized_data_table.clearContents()
        self.normalized_data_table.setRowCount(0)
        self.normalized_data_table.setColumnCount(0)

        if raw_df is not None and not raw_df.empty:
            self.create_table(raw_df, self.raw_data_table)
        if norm_df is not None and not isinstance(norm_df, bool) and not norm_df.empty:
            self.create_table(norm_df, self.normalized_data_table)

        self.export_menu_button.setVisible(True)

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
        # Clear the plot view by setting empty HTML
        self.plot_view.setHtml("<html><body></body></html>")
        self.raw_data_table.clearContents()
        self.raw_data_table.setRowCount(0)
        self.raw_data_table.setColumnCount(0)
        self.normalized_data_table.clearContents()
        self.normalized_data_table.setRowCount(0)
        self.normalized_data_table.setColumnCount(0)
        self.export_menu_button.setVisible(False)

    def handle_download(self, download_item: QWebEngineDownloadItem):
        """
        Handle Plotly's toImage download.
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
        Exports the current data table to JSON file.
        """
        if self.normalized_data_table.rowCount() > 0:
            VisualizationDataExporter.export_table_data_as_json(self.normalized_data_table)
        elif self.raw_data_table.rowCount() > 0:
            VisualizationDataExporter.export_table_data_as_json(self.raw_data_table)
        else:
            QMessageBox.information(self, "No data to export.")
