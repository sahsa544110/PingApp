# ping_tab.py
import time
import socket
import csv
import numpy as np
from PyQt6.QtWidgets import QWidget, QFileDialog
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QThread
from PyQt6.QtMultimedia import QSoundEffect
from ping3 import ping, errors as ping_errors
from custom_dialogs import CustomMessageBox
import qtawesome as qta
# pyqtgraph імпортується в ui.py

# --- Новий імпорт ---
from ui import Ui_PingTab


# --- Клас-воркер (ЛОГІКА) залишається без змін ---
class PingWorker(QThread):
    result_ready = pyqtSignal(dict)
    permission_error = pyqtSignal()

    def __init__(self, host):
        super().__init__()
        self.host = host
        self._is_running = True
        self.seq = 0

    def run(self):
        while self._is_running:
            self.seq += 1
            current_time = time.strftime("%H:%M:%S")
            delay = None
            status = "Failed"  # Встановлюємо за замовчуванням
            error_message = ""

            try:
                delay = ping(self.host, timeout=2, unit="ms")

                # ping() повертає None або False при помилці (напр. timeout)
                if delay is None or delay is False or delay <= 0:
                    delay = -1
                    # error_message тут не потрібен, статус "Failed" це вже показує
                else:
                    status = "Success"
                    delay = round(delay, 1)

            # --- Покращена обробка винятків ---

            # Конкретна помилка: хост не знайдено (DNS-помилка)
            except (socket.gaierror, ping_errors.HostUnknown):
                error_message = "Host not found. Check DNS or network."
                delay = -1

            # Конкретна помилка: немає прав адміністратора
            except ping_errors.PermissionError:
                error_message = "ICMP ping requires administrator privileges."
                delay = -1
                self.permission_error.emit()
                self._is_running = False  # Зупиняємо воркер

            # Інші відомі помилки бібліотеки ping3
            except ping_errors.PingError as e:
                error_message = f"Ping error: {e}"
                delay = -1

            # Загальний обробник для НЕОЧІКУВАНИХ помилок
            except Exception as e:
                error_message = f"An unexpected error occurred: {e}"
                delay = -1
                # Важливо вивести цю помилку в консоль, щоб ви її побачили!
                print(f"[PingWorker Error] Host: {self.host}, Error: {e}")

                # --- Кінець обробки ---

            if not self._is_running:
                break

            result_data = {
                "seq": self.seq,
                "host": self.host,
                "time": current_time,
                "delay": delay,
                "status": status,
                "error_message": error_message
            }
            self.result_ready.emit(result_data)

            if self._is_running:
                self.msleep(1000)

    def stop(self):
        self._is_running = False


class PingTab(QWidget):
    new_ping_result = pyqtSignal(dict)
    ping_started = pyqtSignal()
    ping_status_changed = pyqtSignal(bool)

    def __init__(self, history_callback, completer):
        super().__init__()

        # Створюємо UI
        self.ui = Ui_PingTab()
        self.ui.setupUi(self)

        # Ініціалізуємо логіку
        self.history_callback = history_callback
        self.is_running = False
        self.sound_enabled = False
        self.is_live_view = True

        self.sound_effect = QSoundEffect()
        self.sound_effect.setSource(QUrl.fromLocalFile("loss.wav"))
        self.sound_effect.setVolume(1.0)

        self.full_pings = []
        self.full_times = []
        self.sent = 0
        self.received = 0
        self.worker = None

        # Встановлюємо початковий стиль кнопки
        self.ui.btn.setStyleSheet(self.btn_style("#6750A4"))

        # --- Прив'язка сигналів (ЛОГІКА) ---
        self.ui.input.textEdited.connect(self.stop_ping_keep_data)
        self.ui.input.returnPressed.connect(self.toggle_ping)

        self.ui.sound_btn.clicked.connect(self.toggle_sound)
        self.ui.export_data_btn.clicked.connect(self.export_graph_data)
        self.ui.export_btn.clicked.connect(self.export_screenshot)

        self.ui.btn.clicked.connect(self.toggle_ping)

        self.ui.live_btn.clicked.connect(lambda: self.set_view_mode('live'))
        self.ui.btn_50.clicked.connect(lambda: self.set_view_mode(50))
        self.ui.btn_100.clicked.connect(lambda: self.set_view_mode(100))
        self.ui.all_btn.clicked.connect(lambda: self.set_view_mode('all'))

    def stop_ping_keep_data(self):
        """Останавливает тест, но не очищает график и статистику"""
        if self.is_running:
            self.is_running = False
            if self.worker:
                self.worker.stop()
            self.ui.btn.setText("Start Ping")
            self.ui.btn.setStyleSheet(self.btn_style("#6750A4"))
            self.ping_status_changed.emit(False)

    def mousePressEvent(self, event):
        self.ui.input.clearFocus()
        super().mousePressEvent(event)

    def set_view_mode(self, mode):
        """Handle view mode changes for the graph."""
        self.is_live_view = (mode == 'live')

        sender = self.sender()
        for btn in self.view_buttons:
            if btn is not sender:
                btn.setChecked(False)
        sender.setChecked(True)

        total_points = len(self.full_pings)
        if not self.is_running and total_points == 0: return

        self.ui.chart.enableAutoRange(axis='y')
        if mode == 'live':
            self.ui.chart.setXRange(max(0, total_points - 20), total_points)
        elif mode == 50:
            self.ui.chart.setXRange(max(0, total_points - 50), total_points)
        elif mode == 100:
            self.ui.chart.setXRange(max(0, total_points - 100), total_points)
        elif mode == 'all':
            self.ui.chart.autoRange()

    def show_status_message(self, message):
        self.ui.status_icon.setPixmap(qta.icon("fa5s.exclamation-triangle", color="#FFA000").pixmap(16, 16))
        self.ui.status_text.setText(message)
        self.ui.status_frame.show()

    def handle_ping_result(self, result_data):
        if not self.is_running:
            return

        delay = result_data["delay"]
        error_message = result_data["error_message"]

        if error_message and "Permission" not in error_message:
            self.show_status_message(error_message)
        else:
            self.ui.status_frame.hide()

        if result_data["status"] == "Failed":
            if self.sound_enabled: self.sound_effect.play()
            self.ui.result_icon.setPixmap(qta.icon("mdi.close-circle", color="#B3261E").pixmap(24, 24))
            self.ui.result_text.setText("Request timed out")
            self.ui.result_text.setStyleSheet("color: #B3261E;")
            self.full_pings.append(np.nan)
        else:
            self.ui.result_icon.setPixmap(qta.icon("mdi.check-circle", color="#6750A4").pixmap(24, 24))
            self.ui.result_text.setText(f"{delay} ms")
            self.ui.result_text.setStyleSheet("color: #6750A4;")
            self.received += 1
            self.full_pings.append(delay)

        self.sent = result_data["seq"]
        self.new_ping_result.emit(result_data)
        self.full_times.append(time.time())
        self.update_stats()

    def handle_permission_error(self):
        self.stop_ping_keep_data()
        CustomMessageBox.show_critical(self, "Permission Error",
                                       "ICMP ping requires administrator privileges. Please restart as administrator.")

    def on_worker_finished(self):
        self.worker = None
        if self.is_running:
            self.stop_ping_keep_data()

    def toggle_ping(self):
        if not self.is_running:
            host = self.ui.input.text().strip() or self.ui.input.placeholderText()
            if not host:
                CustomMessageBox.show_warning(self, "Attention", "Please enter a host to ping.")
                return

            self.history_callback(host)
            self.reset_stats()
            self.ping_started.emit()
            self.is_running = True
            self.ui.btn.setText("Stop Ping")
            self.ui.btn.setStyleSheet(self.btn_style("#B3261E"))
            self.ping_status_changed.emit(True)

            self.worker = PingWorker(host)
            self.worker.result_ready.connect(self.handle_ping_result)
            self.worker.permission_error.connect(self.handle_permission_error)
            self.worker.finished.connect(self.on_worker_finished)
            self.worker.start()
        else:
            self.stop_ping_keep_data()

    def reset_stats(self):
        self.full_pings.clear()
        self.full_times.clear()
        self.sent = 0
        self.received = 0
        self.ui.result_text.setText("")
        self.ui.result_icon.setText("      —")
        self.ui.status_frame.hide()
        self.ui.live_btn.setChecked(True)
        self.is_live_view = True
        for btn in [self.ui.btn_50, self.ui.btn_100, self.ui.all_btn]:
            btn.setChecked(False)

        for l in [self.ui.sent_value, self.ui.received_value, self.ui.loss_value, self.ui.min_value, self.ui.max_value,
                  self.ui.avg_value]: l.setText("")
        self.ui.plot_line.setData([], [])
        self.ui.plot_scatter_success.setData([], [])
        self.ui.plot_scatter_loss.setData([], [])

    def update_stats(self):
        if not self.full_pings: return
        total_points = len(self.full_pings)

        p = [p for p in self.full_pings if not np.isnan(p)]
        l = ((self.sent - self.received) / self.sent) * 100 if self.sent > 0 else 0
        self.ui.sent_value.setText(str(self.sent))
        self.ui.received_value.setText(str(self.received))
        self.ui.loss_value.setText(f"{l:.1f}%")
        if p:
            self.ui.min_value.setText(f"{min(p):.1f} ms")
            self.ui.max_value.setText(f"{max(p):.1f} ms")
            self.ui.avg_value.setText(f"{np.mean(p):.1f} ms")

        y = np.array(self.full_pings)
        x = np.arange(total_points)

        if y.size == 0:
            return

        valid_indices = ~np.isnan(y)

        self.ui.plot_line.setData(x[valid_indices], y[valid_indices])
        self.ui.plot_scatter_success.setData(x[valid_indices], y[valid_indices])
        self.ui.plot_scatter_loss.setData(x[~valid_indices], np.zeros(np.sum(~valid_indices)))

        if self.is_live_view:
            self.ui.chart.enableAutoRange(axis='y')
            self.ui.chart.setXRange(max(0, total_points - 20), total_points)

    def btn_style(self, c):
        return f"QPushButton {{ background-color: {c}; color: white; border-radius: 14px; padding: 8px; }} QPushButton:hover {{ background-color: {'#D32F2F' if c == '#B3261E' else '#7F67BE'}; }}"

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            self.ui.sound_btn.setIcon(qta.icon("fa5s.volume-up", color="#6750A4"));
            self.ui.sound_btn.setToolTip("Disable sound")
        else:
            self.ui.sound_btn.setIcon(qta.icon("fa5s.volume-mute", color="#49454F"));
            self.ui.sound_btn.setToolTip("Enable packet loss sound")

    def export_graph_data(self):
        if not self.full_times: CustomMessageBox.show_info(self, "No Data", "There is no data to export."); return
        path, _ = QFileDialog.getSaveFileName(self, "Export Graph Data", "ping_data.csv", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow(["Timestamp", "Latency (ms)"])
                    for ts, latency in zip(self.full_times, self.full_pings):
                        time_str = f"'{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))}"
                        latency_str = f"{latency:.1f}" if not np.isnan(latency) else "Failed"
                        writer.writerow([time_str, latency_str])
            except Exception as e:
                CustomMessageBox.show_critical(self, "Export Error", f"Could not save file: {e}")

    def export_screenshot(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Screenshot", "screenshot.png", "PNG Images (*.png)")
        if path: self.grab().save(path)