from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout,
    QListWidget, QLineEdit, QPushButton
)
from PyQt5.QtCore import pyqtSignal

class SelectionBox(QGroupBox):

    selection_changed = pyqtSignal()

    def __init__(self, title, multi_selection=True, parent=None):
        super().__init__(title, parent)
        self.multi_selection = multi_selection
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_items)
        top_row.addWidget(self.search_bar)

        self.toggle_btn = QPushButton("Select All")
        self.toggle_btn.clicked.connect(self.toggle_all)
        top_row.addWidget(self.toggle_btn)

        layout.addLayout(top_row)

        self.list_widget = QListWidget()

        self.list_widget.setSelectionMode(
            QListWidget.MultiSelection if self.multi_selection else QListWidget.SingleSelection
        )

        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.list_widget)

    def add_items(self, items):
        self.list_widget.addItems(items)
        self.update_toggle_text()

    def clear_items(self):
        self.list_widget.clear()
        self.update_toggle_text()

    def get_selected_items(self):
        return [item.text() for item in self.list_widget.selectedItems()]

    def filter_items(self, text):
        text = text.lower()

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text not in item.text().lower())

    def on_selection_changed(self):
        self.selection_changed.emit()
        self.update_toggle_text()

    def toggle_all(self):
        count = self.list_widget.count()
        selected = len(self.list_widget.selectedItems())

        if selected < count:
            self.list_widget.selectAll()
        else:
            self.list_widget.clearSelection()
        self.update_toggle_text()

    def update_toggle_text(self):
        count = self.list_widget.count()
        selected = len(self.list_widget.selectedItems())

        if count > 0 and selected == count:
            self.toggle_btn.setText("Deselect All")
        else:
            self.toggle_btn.setText("Select All")
