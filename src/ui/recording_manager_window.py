from PyQt5.QtWidgets import (
    QDialog, QPushButton, QListWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QMessageBox, QLineEdit, QFileDialog
)
from PyQt5.QtCore import pyqtSignal
from src.speech_importer import SpeechImporter

class RecordingsManager(QDialog):
    recordings_updated = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.speech_importer = SpeechImporter(db)
        self.setWindowTitle("Manage Recordings")
        self.setMinimumSize(600, 500)
        self.init_ui()
        self.load_recordings()

    def init_ui(self):
        layout = QVBoxLayout()

        # Search Bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter recording ID to search...")
        self.search_input.textChanged.connect(self.filter_recordings)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Recordings list
        self.recordings_list = QListWidget()
        self.recordings_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.recordings_list)

        # Buttons layout
        buttons_layout = QHBoxLayout()

        self.import_btn = QPushButton("Import Files")
        self.import_btn.clicked.connect(self.import_files)
        buttons_layout.addWidget(self.import_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected_recordings)
        self.delete_btn.setEnabled(False)
        buttons_layout.addWidget(self.delete_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

        self.recordings_list.itemSelectionChanged.connect(self.on_selection_changed)

    def load_recordings(self):
        """
        Load all recordings from the database to the list widget.
        """
        self.recordings_list.clear()
        try:
            recordings = self.db.get_all_recordings()
            self.recordings_list.addItems(recordings)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load recordings: {str(e)}")

    def filter_recordings(self, text):
        """
        Filter the recordings list based on the search input.
        """
        for index in range(self.recordings_list.count()):
            item = self.recordings_list.item(index)
            item.setHidden(text.lower() not in item.text().lower())

    def on_selection_changed(self):
        """
        Enable delete button if at least one item is selected.
        """
        self.delete_btn.setEnabled(bool(self.recordings_list.selectedItems()))

    def delete_selected_recordings(self):
        """
        Delete the selected recordings after user confirmation.
        """
        selected_items = self.recordings_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select at least one recording to delete.")
            return

        recording_ids = [item.text().strip() for item in selected_items]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the selected {len(recording_ids)} recordings? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        try:
            deletion_results = self.db.delete_recordings(recording_ids)
            total_deleted = sum(result.get('deleted_count', 0) for result in deletion_results.values())

            QMessageBox.information(
                self,
                "Deletion Successful",
                f"Successfully deleted {total_deleted} documents across collections."
            )
            self.recordings_updated.emit()
            self.load_recordings()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Deletion Failed",
                f"Error while deleting recordings: {str(e)}"
            )

    def import_files(self):
        """
        Allows user to select audio and TextGrid files and imports them using SpeechImporter.
        """
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio and TextGrid Files", "", "Audio and TextGrid Files (*.wav *.TextGrid);;All Files (*)"
        )

        if files:
            try:
                missing_pairs = self.speech_importer.import_files(files)
                self.load_recordings()
                if missing_pairs:
                    QMessageBox.warning(
                        self,
                        'Warning',
                        f"The following files are missing their pairs: {', '.join(missing_pairs)}"
                    )
                QMessageBox.information(self, 'Success', "File import completed.")
                self.recordings_updated.emit()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f"File import failed: {str(e)}")
        else:
            QMessageBox.information(self, 'Info', "No files selected for import.")
