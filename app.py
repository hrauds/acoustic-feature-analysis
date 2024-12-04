import atexit
import sys
import logging
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.database import Database
from config import USE_MONGO_MOCK

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)

    # Initialize the database
    db = Database()

    # Initialize sample data if using mongomock
    if USE_MONGO_MOCK:
        db.initialize_sample_data()

    app = QApplication(sys.argv)
    window = MainWindow(db)
    window.show()
    atexit.register(db.close_connection)
    sys.exit(app.exec_())
