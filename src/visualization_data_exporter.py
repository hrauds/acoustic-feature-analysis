import json
from PyQt5.QtWidgets import QFileDialog, QMessageBox


class VisualizationDataExporter:

    @staticmethod
    def export_table_data_as_json(table_widget):
        """
        Exports data from a QTableWidget to a JSON file.

        :param table_widget: The QTableWidget instance to export data from.
        """
        try:
            data = []
            headers = [table_widget.horizontalHeaderItem(col).text() for col in range(table_widget.columnCount())]

            for row in range(table_widget.rowCount()):
                row_data = {}
                for col in range(table_widget.columnCount()):
                    item = table_widget.item(row, col)
                    row_data[headers[col]] = item.text() if item else ""
                data.append(row_data)

            json_data = {
                "data" : data
            }

            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                table_widget,
                "Export Data as JSON",
                "",
                "JSON Files (*.json)",
                options=options
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as json_file:
                    json.dump(json_data, json_file, indent=4)
                QMessageBox.information(table_widget, "Success", f"JSON data exported to {file_path}")

        except Exception as e:
            QMessageBox.critical(table_widget, "Error", f"Failed to export JSON data: {str(e)}")
