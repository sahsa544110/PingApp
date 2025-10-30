# ip_test_tab.py
import csv
import socket
import time
from PyQt6.QtWidgets import (
    QWidget, QTableWidgetItem, QFileDialog, QApplication
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import qtawesome as qta
# --- Змінено імпорт ---
from icmplib import ping, exceptions as icmp_exceptions

# --- Новий імпорт ---
from ui import Ui_IPTestTab


# --- Логічні класи (без змін) ---
class NumericTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            self_val = float(self.text())
        except:
            self_val = float('inf')
        try:
            other_val = float(other.text())
        except:
            other_val = float('inf')
        return self_val < other_val


class IPStat:
    def __init__(self):
        self.sent = 0
        self.received = 0


class IPTestWorker(QThread):
    result_ready = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, addresses_to_test):
        super().__init__()
        self.addresses = addresses_to_test
        self._is_running = True

    # --- ОНОВЛЕНИЙ МЕТОД RUN З КРАЩИМИ ВИНЯТКАМИ ---
    def run(self):
        while self._is_running:
            for address in self.addresses:
                if not self._is_running:
                    break

                result = {}  # Створюємо порожній словник

                try:
                    host_stats = ping(address, count=1, timeout=1)
                    result = {
                        "address": address,
                        "rtt": host_stats.avg_rtt if host_stats.is_alive else 0,
                        "is_alive": host_stats.is_alive,
                        "status_text": "Success" if host_stats.is_alive else "Failed"
                    }

                # --- Покращена обробка винятків ---

                # Конкретна помилка: немає прав
                except (icmp_exceptions.SocketPermissionError, PermissionError):
                    result = {"address": address, "is_alive": False, "status_text": "Permission Error"}
                    self._is_running = False  # Зупиняємо весь тест

                # Конкретна помилка: хост не знайдено (DNS)
                except icmp_exceptions.NameLookupError:
                    result = {"address": address, "is_alive": False, "status_text": "Host not found"}

                # Конкретна помилка: неправильний формат адреси
                except icmp_exceptions.SocketAddressError:
                    result = {"address": address, "is_alive": False, "status_text": "Invalid address"}

                # Інші відомі помилки бібліотеки icmplib
                except icmp_exceptions.ICMPLibError as e:
                    result = {"address": address, "is_alive": False, "status_text": f"ICMP Error"}
                    print(f"[IPTestWorker ICMP Error] Host: {address}, Error: {e}")

                # Загальний обробник для НЕОЧІКУВАНИХ помилок
                except Exception as e:
                    result = {"address": address, "is_alive": False, "status_text": "Unexpected Error"}
                    print(f"[IPTestWorker Error] Host: {address}, Error: {e}")

                # --- Кінець обробки ---

                self.result_ready.emit(result)

            if self._is_running:
                time.sleep(1)

        self.finished.emit()

    def stop(self):
        self._is_running = False


# --- Оновлений клас вкладки ---
class IPTestTab(QWidget):
    def __init__(self, history_callback, completer):
        super().__init__()

        # Створюємо UI
        self.ui = Ui_IPTestTab()
        self.ui.setupUi(self)

        # Ініціалізуємо логіку
        self.worker = None
        self.host_stats = {}
        self.history_callback = history_callback

        # Встановлюємо початковий стиль кнопки
        self.set_start_button_style(False)

        # --- Прив'язка сигналів (ЛОГІКА) ---
        self.ui.host_input.returnPressed.connect(self.add_host_from_input)
        self.ui.add_btn.clicked.connect(self.add_host_from_input)
        self.ui.import_btn.clicked.connect(self.import_hosts)
        self.ui.copy_btn.clicked.connect(self.copy_selection)
        self.ui.delete_btn.clicked.connect(self.delete_selection)  # --- *** НОВИЙ СИГНАЛ *** ---
        self.ui.start_btn.clicked.connect(self.toggle_test)
        self.ui.export_btn.clicked.connect(self.export_results)

    # --- *** НОВИЙ МЕТОД *** ---
    def delete_selection(self):
        """
        Видаляє вибрані рядки з таблиці та з активного тестування.
        """
        selected_items = self.ui.table.selectedItems()
        if not selected_items:
            return  # Нічого не вибрано

        # Отримуємо унікальні індекси рядків, відсортовані у зворотному порядку.
        # Це важливо, щоб індекси не зсувалися під час видалення.
        rows_to_delete = sorted(list(set(item.row() for item in selected_items)), reverse=True)

        hosts_removed = []

        # Тимчасово вимикаємо сортування, щоб уникнути помилок при видаленні
        self.ui.table.setSortingEnabled(False)

        for row in rows_to_delete:
            host_item = self.ui.table.item(row, 0)
            if host_item:
                host = host_item.text()
                hosts_removed.append(host)

                # Видаляємо хост зі словника статистики
                if host in self.host_stats:
                    del self.host_stats[host]

            # Видаляємо рядок з таблиці (візуально)
            self.ui.table.removeRow(row)

        # Вмикаємо сортування назад
        self.ui.table.setSortingEnabled(True)

        # Якщо воркер активний, видаляємо хости з його списку завдань
        if self.worker and self.worker.isRunning() and hosts_removed:
            self.worker.addresses = [addr for addr in self.worker.addresses if addr not in hosts_removed]

    # --- *** КІНЕЦЬ НОВОГО МЕТОДУ *** ---

    def copy_selection(self):
        selection = self.ui.table.selectedIndexes()
        if not selection:
            return
        rows = sorted(set(index.row() for index in selection))
        clipboard_text = []
        for row in rows:
            row_data = [self.ui.table.item(row, col).text() for col in range(self.ui.table.columnCount())]
            clipboard_text.append("\t".join(row_data))
        QApplication.clipboard().setText("\n".join(clipboard_text))

    def add_host_from_input(self):
        address = self.ui.host_input.text().strip()
        if not address:
            return
        self.history_callback(address)
        self._add_row(address)
        self.ui.host_input.clear()

        if self.worker and self.worker.isRunning():
            if address not in self.worker.addresses:
                self.worker.addresses.append(address)
                self.host_stats[address] = IPStat()

    def _add_row(self, address):
        for row in range(self.ui.table.rowCount()):
            if self.ui.table.item(row, 0).text() == address:
                return
        row_position = self.ui.table.rowCount()
        self.ui.table.insertRow(row_position)
        self.ui.table.setItem(row_position, 0, QTableWidgetItem(address))
        self.ui.table.setItem(row_position, 1, QTableWidgetItem("-"))
        self.ui.table.setItem(row_position, 2, NumericTableWidgetItem("-"))
        self.ui.table.setItem(row_position, 3, NumericTableWidgetItem("-"))
        for col in range(4):
            if col > 0:
                self.ui.table.item(row_position, col).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        if self.worker and self.worker.isRunning():
            self.host_stats[address] = IPStat()

    def toggle_test(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.ui.start_btn.setEnabled(False)
            self.ui.start_btn.setText("Stopping...")
        elif self.worker is None:
            if self.ui.host_input.text().strip():
                self.add_host_from_input()
            addresses = []
            self.host_stats.clear()
            for row in range(self.ui.table.rowCount()):
                item = self.ui.table.item(row, 0)
                if item:
                    address = item.text()
                    addresses.append(address)
                    self.host_stats[address] = IPStat()
            if not addresses:
                return
            self.set_start_button_style(True)
            self.worker = IPTestWorker(addresses)
            self.worker.result_ready.connect(self.update_row)
            self.worker.finished.connect(self.on_test_finished)
            self.worker.start()

    def update_row(self, result):
        address = result["address"]
        if address not in self.host_stats:
            # Хост міг бути видалений, поки воркер ще працював
            return
        self.ui.table.setSortingEnabled(False)
        for row in range(self.ui.table.rowCount()):
            if self.ui.table.item(row, 0).text() == address:
                stat = self.host_stats[address]
                stat.sent += 1
                status_text = "Success"
                latency_item = NumericTableWidgetItem("-")
                if result.get("is_alive"):
                    stat.received += 1
                    latency_item.setText(f"{result['rtt']:.2f}")
                else:
                    status_text = result.get("status_text", "Failed")
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(QColor("#1D672D" if result.get("is_alive") else "#B3261E"))
                loss_percent = (1 - stat.received / stat.sent) * 100 if stat.sent > 0 else 0
                loss_item = NumericTableWidgetItem(f"{loss_percent:.1f}")
                self.ui.table.setItem(row, 1, status_item)
                self.ui.table.setItem(row, 2, latency_item)
                self.ui.table.setItem(row, 3, loss_item)
                for col in range(self.ui.table.columnCount()):
                    if self.ui.table.item(row, col) and col > 0:
                        self.ui.table.item(row, col).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                break
        current_sort_col = self.ui.table.horizontalHeader().sortIndicatorSection()
        current_sort_order = self.ui.table.horizontalHeader().sortIndicatorOrder()
        self.ui.table.sortItems(current_sort_col, current_sort_order)
        self.ui.table.setSortingEnabled(True)

    def on_test_finished(self):
        self.set_start_button_style(False)
        self.ui.start_btn.setEnabled(True)
        self.worker = None

    def set_start_button_style(self, is_running):
        btn_font = QFont("Segoe UI Semibold", 10)
        base_style = """
            QPushButton {
                border-radius: 12px;
                padding: 6px 12px;
                font-weight: 600;
            }
        """
        if is_running:
            self.ui.start_btn.setText("Stop Test")
            self.ui.start_btn.setIcon(qta.icon("fa5s.stop", color="white"))
            self.ui.start_btn.setStyleSheet(base_style + """
                QPushButton {
                    background-color: #B3261E;
                    color: white;
                    border: 1px solid #B3261E;
                }
                QPushButton:hover { background-color: #D32F2F; }
            """)
        else:
            self.ui.start_btn.setText(" Start Test")
            self.ui.start_btn.setIcon(qta.icon("fa5s.play", color="white"))
            self.ui.start_btn.setStyleSheet(base_style + """
                QPushButton {
                    background-color: #6750A4;
                    color: white;
                    border: 1px solid #6750A4;
                }
                QPushButton:hover { background-color: #7F67BE; }
            """)
        self.ui.start_btn.setFont(btn_font)

    def import_hosts(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Hosts", "", "Text Files (*.txt);;All Files (*)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        address = line.strip()
                        if address:
                            self.history_callback(address)
                            self._add_row(address)
            except Exception as e:
                print(f"Error importing file: {e}")

    def export_results(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Results", "ip_test_results.csv", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(
                        [self.ui.table.horizontalHeaderItem(i).text() for i in range(self.ui.table.columnCount())])
                    for row in range(self.ui.table.rowCount()):
                        writer.writerow(
                            [self.ui.table.item(row, col).text() for col in range(self.ui.table.columnCount())])
            except Exception as e:
                print(f"Error exporting file: {e}")