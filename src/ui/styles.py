MAIN_WINDOW_STYLE="""
    QWidget {
        background-color: #f5f5f5;
        font-size: 12px;
    }

    QLabel {
        color: #333333;
    }

    QPushButton {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #cccccc;
        padding: 8px 16px;
        border-radius: 6px;
        transition: background-color 0.2s, color 0.2s, border 0.2s, box-shadow 0.2s;
    }
    
    QPushButton::menu-indicator {
        image: url('');
    }

    QPushButton:hover {
        background-color: #e0e0e0;
        color: #2980b9;
        border: 1px solid #2980b9;
        box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.05);
    }

    QPushButton:pressed {
        background-color: #d5d5d5;
        color: #333333;
        border: 1px solid #95a5a6;
        box-shadow: inset 0px 1px 2px rgba(0, 0, 0, 0.1);
    }

    /* Radio Buttons */
    QRadioButton {
        color: #333333;
        spacing: 8px;
    }

    QRadioButton::indicator {
        width: 14px;
        height: 14px;
    }

    QRadioButton::indicator:checked {
        background-color: #2980b9;
        border: 1px solid #2980b9;
        border-radius: 8px;
    }

    QRadioButton::indicator:unchecked {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 8px;
    }

    QListWidget {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 6px;
        padding: 6px;
    }

    QListWidget::item:selected {
        background-color: #2980b9;
        color: #ffffff;
    }

    QListWidget::item:hover {
        background-color: #2980b9;
        color: #333333;
    }

    QTableWidget {
        background-color: #ffffff;
        gridline-color: #e0e0e0;
        border: 1px solid #cccccc;
        border-radius: 6px;
    }

    QTableWidget::item:selected {
        background-color: #2980b9;
        color: #ffffff;
        border-radius: 4px;
    }

    QTableWidget::item:hover {
        background-color: #f0f0f0;
        color: #333333;
    }

    QSplitter::handle {
        background-color: #cccccc;
        width: 6px;
        border-radius: 3px;
    }

    QMenu {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 4px;
        padding: 5px 0px;
    }

    QMenu::item {
        padding: 8px 20px;
        color: #333333;
    }

    QMenu::item:selected {
        background-color: #2980b9;
        color: #ffffff;
    }

    QScrollBar:vertical {
        background: #f5f5f5;
        width: 12px;
        margin: 0px 0px 0px 0px;
    }

    QScrollBar::handle:vertical {
        background: #cccccc;
        min-height: 20px;
        border-radius: 6px;
    }

    QScrollBar::handle:vertical:hover {
        background: #b3b3b3;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: none;
        height: 0px;
    }

    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }

    QLineEdit {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }

    QLineEdit:focus {
        border: 1px solid #2980b9;
        box-shadow: 0px 0px 5px rgba(41, 128, 185, 0.2);
    }

    QComboBox {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }

    QComboBox:hover {
        border: 1px solid #2980b9;
    }

    QMenuBar {
        background-color: #f5f5f5;
        color: #333333;
        padding: 5px;
        font-size: 12px;
    }

    QMenuBar::item {
        padding: 8px 12px;
    }

    QMenuBar::item:selected {
        background-color: #2980b9;
        color: #ffffff;
    }

    QWidget::tooltip {
        background-color: #333333;
        color: #ffffff;
        border: 1px solid #cccccc;
        padding: 5px;
        border-radius: 4px;
        font-size: 12px;
    }

    QStatusBar {
        background-color: #f5f5f5;
        color: #333333;
        font-size: 12px;
    }

    QTabWidget::pane {
        border: 1px solid #cccccc;
        background-color: #ffffff;
        border-radius: 6px;
    }

    QTabBar::tab {
        background: #ecf0f1;
        border: 1px solid #cccccc;
        padding: 10px 20px;
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        margin-right: 2px;
        font-size: 12px;
    }

    QTabBar::tab:selected, QTabBar::tab:hover {
        background: #ffffff;
        border-color: #2980b9;
        color: #2980b9;
    }

    QTabBar::tab:selected {
        position: relative;
        top: 1px;
    }
"""
