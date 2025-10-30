# custom_dialogs.py
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QFont
import qtawesome as qta

class CustomMessageBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QMessageBox {
                background-color: #FDFBFF;
            }
            QLabel#qt_msgbox_label { /* Title Label */
                color: #1C1B1F;
                font-size: 16px;
                font-weight: bold;
            }
            QLabel#qt_msgboxex_label { /* Content Text Label */
                color: #49454F;
                font-size: 14px;
            }
            QPushButton {
                background-color: #6750A4;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #7F67BE;
            }
            QPushButton:pressed {
                background-color: #4F378B;
            }
        """)

    @staticmethod
    def show_message(parent, title, text, icon):
        msg_box = CustomMessageBox(parent)
        msg_box.setIcon(icon)
        msg_box.setText(title)
        msg_box.setInformativeText(text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    @staticmethod
    def show_info(parent, title, text):
        CustomMessageBox.show_message(parent, title, text, QMessageBox.Icon.Information)

    @staticmethod
    def show_warning(parent, title, text):
        CustomMessageBox.show_message(parent, title, text, QMessageBox.Icon.Warning)

    @staticmethod
    def show_critical(parent, title, text):
        CustomMessageBox.show_message(parent, title, text, QMessageBox.Icon.Critical)