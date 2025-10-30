# main.py
import sys
# --- Змінено цей рядок ---
from PyQt6.QtWidgets import QApplication, QWidget, QCompleter
from PyQt6.QtCore import Qt, QStringListModel

# --- Нові імпорти ---
from custom_navbar import CustomNavBar  # Імпортуємо логіку
from ping_tab import PingTab
from table_tab import TableTab
from ip_test_tab import IPTestTab
from ui import Ui_MainWindow           # Імпортуємо UI головного вікна

MAX_HISTORY_ITEMS = 100

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Ініціалізуємо не-UI дані
        self.history = []
        self.history_model = QStringListModel()
        self.history_model.setStringList(self.history)
        self.completer = QCompleter() # <--- Тепер цей рядок буде працювати
        self.completer.setModel(self.history_model)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)

        # Створюємо екземпляри наших вкладок та навігації
        # Вони потрібні до setupUi, щоб ui.py міг їх додати у QStackedWidget
        self.ping_widget = PingTab(self.add_to_history, self.completer)
        self.table_widget = TableTab()
        self.ip_test_widget = IPTestTab(self.add_to_history, self.completer)
        self.navbar = CustomNavBar()

        # Створюємо та налаштовуємо UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # --- З'єднуємо сигнали (ЛОГІКА) ---
        self.ui.navbar.tab_changed.connect(self.ui.pages.setCurrentIndex)

        # З'єднання сигналів між сторінками
        self.ping_widget.ping_started.connect(self.table_widget.clear_table)
        self.ping_widget.new_ping_result.connect(self.table_widget.add_ping_result)
        self.table_widget.toggle_ping_requested.connect(self.ping_widget.toggle_ping)
        self.ping_widget.ping_status_changed.connect(self.table_widget.update_toggle_button_style)

    def add_to_history(self, item):
        item = item.strip().lower()
        if item:
            if item in self.history:
                self.history.remove(item)
            self.history.insert(0, item)
            if len(self.history) > MAX_HISTORY_ITEMS:
                self.history = self.history[:MAX_HISTORY_ITEMS]
            self.history_model.setStringList(self.history)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())