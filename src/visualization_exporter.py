import json

class VisualizationExporter:
    @staticmethod
    def save_canvas_as_image(canvas, file_path):
        try:
            canvas.figure.savefig(file_path, dpi=300)
        except Exception as e:
            raise RuntimeError(f"Failed to save visualization: {str(e)}")

    @staticmethod
    def export_table_data_as_json(raw_data_table, normalized_data_table, file_path):
        try:
            raw_data = VisualizationExporter.get_table_data_as_dict(raw_data_table)
            normalized_data = VisualizationExporter.get_table_data_as_dict(normalized_data_table)
            data = {
                "raw_data": raw_data,
                "normalized_data": normalized_data
            }
            with open(file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
        except Exception as e:
            raise RuntimeError(f"Failed to export data: {str(e)}")

    @staticmethod
    def get_table_data_as_dict(table_widget):
        data = []
        for row in range(table_widget.rowCount()):
            row_data = {}
            for col in range(table_widget.columnCount()):
                header = table_widget.horizontalHeaderItem(col).text()
                item = table_widget.item(row, col)
                row_data[header] = item.text() if item else None
            data.append(row_data)
        return data
