# table_tab.py
import csv
import time
from PyQt6.QtWidgets import (
    QWidget, QTableWidgetItem, QFileDialog, QApplication
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta

# --- Новий імпорт ---
from ui import Ui_TableTab


class TableTab(QWidget):
    toggle_ping_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Створюємо UI
        self.ui = Ui_TableTab()
        self.ui.setupUi(self)

        # Встановлюємо початковий стиль
        self.update_toggle_button_style(False)

        # --- Прив'язка сигналів (ЛОГІКА) ---
        self.ui.copy_btn.clicked.connect(self.copy_selection)
        self.ui.toggle_btn.clicked.connect(self.toggle_ping_requested.emit)
        self.ui.export_btn.clicked.connect(self.export_to_csv)

    def update_toggle_button_style(self, is_running):
        if is_running:
            self.ui.toggle_btn.setText("Stop Ping")
            self.ui.toggle_btn.setIcon(qta.icon("mdi.stop", color="white"))
            self.ui.toggle_btn.setStyleSheet("""
                QPushButton { background-color: #B3261E; color: white; border: none; border-radius: 12px; padding: 6px 12px; }
                QPushButton:hover { background-color: #D32F2F; }
            """)
        else:
            self.ui.toggle_btn.setText("Start Ping")
            self.ui.toggle_btn.setIcon(qta.icon("mdi.play", color="white"))
            self.ui.toggle_btn.setStyleSheet("""
                QPushButton { background-color: #6750A4; color: white; border: none; border-radius: 12px; padding: 6px 12px; }
                QPushButton:hover { background-color: #7F67BE; }
            """)

    def add_ping_result(self, data: dict):
        self.ui.table.insertRow(0)

        seq = QTableWidgetItem(str(data.get("seq", "")))
        timestamp = QTableWidgetItem(data.get("time", ""))
        host = QTableWidgetItem(data.get("host", ""))
        status = QTableWidgetItem(data.get("status", ""))
        delay = QTableWidgetItem(str(data.get("delay", "")))

        for item in [seq, timestamp, host, status, delay]:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        if data.get("status") == "Success":
            status.setForeground(QColor("#1D672D"))
            delay_val = data.get("delay")
            delay.setText(f"{delay_val:.1f}")
        else:
            status.setForeground(QColor("#B3261E"))
            delay.setText("—")

        self.ui.table.setItem(0, 0, seq)
        self.ui.table.setItem(0, 1, timestamp)
        self.ui.table.setItem(0, 2, host)
        self.ui.table.setItem(0, 3, status)
        self.ui.table.setItem(0, 4, delay)

    def clear_table(self):
        self.ui.table.setRowCount(0)

    def copy_selection(self):
        selection = self.ui.table.selectedIndexes()
        if not selection:
            return
        rows = sorted(list(set(index.row() for index in selection)))
        clipboard_text = []
        for row in rows:
            row_data = [self.ui.table.item(row, col).text() for col in range(self.ui.table.columnCount())]
            clipboard_text.append("\t".join(row_data))
        QApplication.clipboard().setText("\n".join(clipboard_text))

    def export_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export to CSV", f"ping_history.csv", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file, delimiter=';')
                    headers = [self.ui.table.horizontalHeaderItem(i).text() for i in range(self.ui.table.columnCount())]
                    writer.writerow(headers)

                    for row in range(self.ui.table.rowCount()):
                        row_data = [self.ui.table.item(row, col).text() for col in range(self.ui.table.columnCount())]
                        if len(row_data) > 1:
                            row_data[1] = f"'{row_data[1]}"
                        writer.writerow(row_data)
            except Exception as e:
                print(f"Error exporting to CSV: {e}")