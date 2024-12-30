import atexit
import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from src.ui.main_window import MainWindow
from src.database import Database
from config import USE_MONGO_MOCK
from src.ui.styles import MAIN_WINDOW_STYLE

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)

    # Initialize the database
    db = Database()

    # Initialize sample data if using mongomock
    if USE_MONGO_MOCK:
        db.initialize_sample_data()

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    global_font = QFont('Arial', 12)
    app.setFont(global_font)

    app.setStyleSheet(MAIN_WINDOW_STYLE)

    window = MainWindow(db)
    window.show()
    atexit.register(db.close_connection)
    sys.exit(app.exec_())
