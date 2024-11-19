import sys
import logging
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
