# custom_navbar.py
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal

# --- Новий імпорт ---
from ui import Ui_CustomNavBar


class CustomNavBar(QWidget):
    """
    Спеціальна панель навігації, що замінює стандартний QTabBar.
    Використовує кнопки з іконками та текстом для перемикання сторінок.
    """
    # Сигнал, що відправляється при натисканні кнопки з індексом сторінки
    tab_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        # Створюємо UI
        self.ui = Ui_CustomNavBar()
        self.ui.setupUi(self)

        # --- Прив'язка сигналів (ЛОГІКА) ---
        # Підключаємо сигнал від групи кнопок до нашого кастомного сигналу
        self.ui.button_group.idClicked.connect(self.tab_changed.emit)

    # Функція _create_nav_button тепер є частиною Ui_CustomNavBar
    # і не потрібна тут