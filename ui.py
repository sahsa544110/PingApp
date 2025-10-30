# ui.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QStackedWidget, QCompleter, QLineEdit,
    QPushButton, QLabel, QGraphicsDropShadowEffect, QHBoxLayout, QFrame,
    QGridLayout, QTableWidget, QHeaderView, QTableWidgetItem, QButtonGroup
)
from PyQt6.QtGui import QFont, QIcon, QColor
from PyQt6.QtCore import Qt, QStringListModel, QSize
import qtawesome as qta
import pyqtgraph as pg


# --- Імпорти для класів вкладок (потрібні для type hinting) ---
# Ми не можемо імпортувати їх напряму, щоб уникнути циклічного імпорту,
# тому використаємо 'forward references' у вигляді рядків, якщо знадобиться.
# Але для setupUi(self, ParentWidget) це не обов'язково.

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setWindowTitle("Ping Tool")
        MainWindow.setWindowIcon(QIcon("app.ico"))
        MainWindow.resize(400, 600)

        # Головний вертикальний лейаут
        main_layout = QVBoxLayout(MainWindow)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)  # Прибираємо відступ між віджетами

        # QStackedWidget буде містити всі наші сторінки
        self.pages = QStackedWidget()

        # Створюємо віджети сторінок
        # Вони будуть створені у __init__ MainWindow
        self.ping_widget = MainWindow.ping_widget
        self.table_widget = MainWindow.table_widget
        self.ip_test_widget = MainWindow.ip_test_widget

        # Додаємо сторінки до QStackedWidget
        self.pages.addWidget(self.ping_widget)
        self.pages.addWidget(self.table_widget)
        self.pages.addWidget(self.ip_test_widget)

        # Створюємо та додаємо нашу нову панель навігації
        self.navbar = MainWindow.navbar

        # Додаємо сторінки та панель навігації до головного лейауту
        main_layout.addWidget(self.pages, 1)
        main_layout.addWidget(self.navbar)

        # Загальний фон вікна встановлюється тут
        MainWindow.setStyleSheet("""
            QWidget {
                background-color: #FDFBFF;
            }
            QCompleter QAbstractItemView {
                background-color: #F3EDF7; border: 1px solid #CAC4D0;
                border-radius: 8px; font-size: 14px; color: #49454F;
            }
            QCompleter QAbstractItemView::item { padding: 4px 8px; }
            QCompleter QAbstractItemView::item:selected {
                background-color: #EADDFF; color: #21005D;
            }
            QScrollBar:vertical {
                border: none; background: #EADDFF; width: 10px;
                margin: 0px; border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #6750A4; border-radius: 5px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #7F67BE; }
            QScrollBar:horizontal {
                border: none; background: #EADDFF; height: 10px;
                margin: 0px; border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #6750A4; border-radius: 5px; min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover { background: #7F67BE; }
        """)


class Ui_PingTab(object):
    def setupUi(self, PingTab):
        PingTab.setStyleSheet("background-color: #FDFBFF;")

        layout = QVBoxLayout(PingTab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(5)

        self.input = QLineEdit()
        self.input.setPlaceholderText("google.com")
        self.input.setFont(QFont("Segoe UI", 11))
        self.input.setClearButtonEnabled(True)
        self.input.setStyleSheet("""
            QLineEdit { background-color: #FFFFFF; border: 2px solid #CAC4D0; border-radius: 12px; padding: 6px; color: #1C1B1F; }
            QLineEdit:focus { border: 2px solid #6750A4; }
        """)

        self.sound_btn = QPushButton()
        self.sound_btn.setIcon(qta.icon("fa5s.volume-mute", color="#49454F"))
        self.sound_btn.setToolTip("Enable packet loss sound")

        self.export_data_btn = QPushButton()
        self.export_data_btn.setIcon(qta.icon("fa5s.file-csv", color="#49454F"))
        self.export_data_btn.setToolTip("Export graph data to CSV")

        self.export_btn = QPushButton()
        self.export_btn.setIcon(qta.icon("mdi.camera", color="#49454F"))
        self.export_btn.setToolTip("Save screenshot of the tab")

        for btn in [self.sound_btn, self.export_data_btn, self.export_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background-color: #EADDFF; border-radius: 10px; padding: 4px; }
                QPushButton:hover { background-color: #D0BCFF; }
            """)
            btn.setFixedSize(32, 32)

        controls_layout.addWidget(self.input)
        controls_layout.addWidget(self.sound_btn)
        controls_layout.addWidget(self.export_data_btn)
        controls_layout.addWidget(self.export_btn)

        self.btn = QPushButton("Start Ping")
        self.btn.setFont(QFont("Segoe UI Semibold", 11))
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # Стиль буде встановлено в логіці
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.btn.setGraphicsEffect(shadow)

        self.result_icon = QLabel("")
        self.result_text = QLabel("")
        self.result_text.setFont(QFont("Segoe UI Semibold", 12))
        self.result_text.setStyleSheet("color: #1D1B20;")
        result_layout = QHBoxLayout()
        result_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_layout.setSpacing(8)
        result_layout.addWidget(self.result_icon)
        result_layout.addWidget(self.result_text)

        self.stats_frame = QFrame()
        self.stats_frame.setStyleSheet("QFrame { background-color: #ECE6F0; border-radius: 16px; padding: 4px; }")
        stats_layout = QGridLayout()
        stats_layout.setContentsMargins(0, 16, 0, 16)
        stats_layout.setHorizontalSpacing(0)
        stats_layout.setVerticalSpacing(0)
        font_label = QFont("Segoe UI", 8)
        font_value = QFont("Segoe UI Semibold", 11)

        def stat_item(name):
            t = QLabel(name)
            t.setFont(font_label)
            t.setStyleSheet("color: #49454F;")
            t.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            v = QLabel("")
            v.setFont(font_value)
            v.setStyleSheet("color: #1C1B1F;")
            v.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            return t, v

        self.sent_label, self.sent_value = stat_item("Sent")
        self.received_label, self.received_value = stat_item("Received")
        self.loss_label, self.loss_value = stat_item("Loss")
        self.min_label, self.min_value = stat_item("Min")
        self.max_label, self.max_value = stat_item("Max")
        self.avg_label, self.avg_value = stat_item("Avg")
        stats_layout.addWidget(self.sent_label, 0, 0)
        stats_layout.addWidget(self.sent_value, 1, 0)
        stats_layout.addWidget(self.received_label, 0, 1)
        stats_layout.addWidget(self.received_value, 1, 1)
        stats_layout.addWidget(self.loss_label, 0, 2)
        stats_layout.addWidget(self.loss_value, 1, 2)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: rgba(0, 0, 0, 0.10); border: none;")

        line_layout = QVBoxLayout()
        line_layout.setContentsMargins(0, 10, 0, 10)
        line_layout.addWidget(line)

        line_container = QWidget()
        line_container.setStyleSheet("background-color: #ece6f0;")
        line_container.setLayout(line_layout)

        stats_layout.addWidget(line_container, 2, 0, 1, 3)

        stats_layout.addWidget(self.min_label, 3, 0)
        stats_layout.addWidget(self.min_value, 4, 0)
        stats_layout.addWidget(self.max_label, 3, 1)
        stats_layout.addWidget(self.max_value, 4, 1)
        stats_layout.addWidget(self.avg_label, 3, 2)
        stats_layout.addWidget(self.avg_value, 4, 2)
        self.stats_frame.setLayout(stats_layout)

        self.status_frame = QFrame()
        self.status_frame.setStyleSheet(
            "QFrame { background-color: #FFF8E1; border: 1px solid #FFECB3; border-radius: 8px; }")
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(10, 5, 10, 5)
        self.status_icon = QLabel()
        self.status_text = QLabel()
        self.status_text.setFont(QFont("Segoe UI", 9))
        self.status_text.setStyleSheet("color: #6D4C41; border: none; background: transparent;")
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_text, 1)
        self.status_frame.setLayout(status_layout)
        self.status_frame.hide()

        view_controls_layout = QHBoxLayout()
        btn_font = QFont("Segoe UI", 9)
        btn_style = """
            QPushButton { background-color: #F3EDF7; color: #49454F; border: 1px solid #CAC4D0; border-radius: 8px; padding: 4px 8px; }
            QPushButton:hover { background-color: #E8DEF8; }
            QPushButton:checked { background-color: #D0BCFF; border-color: #6750A4; }
        """
        self.live_btn = QPushButton("Live (20)")
        self.btn_50 = QPushButton("50")
        self.btn_100 = QPushButton("100")
        self.all_btn = QPushButton("All")

        PingTab.view_buttons = [self.live_btn, self.btn_50, self.btn_100, self.all_btn]
        for btn in PingTab.view_buttons:
            btn.setFont(btn_font)
            btn.setStyleSheet(btn_style)
            btn.setCheckable(True)
            view_controls_layout.addWidget(btn)

        self.live_btn.setChecked(True)

        self.chart = pg.PlotWidget()
        self.chart.hideButtons()
        self.chart.setBackground('w')
        self.chart.showGrid(x=True, y=True, alpha=0.2)
        self.chart.setContentsMargins(0, 0, 0, 0)
        self.plot_line = self.chart.plot([], [], pen=pg.mkPen('#6750A4', width=2))
        self.plot_scatter_success = pg.ScatterPlotItem([], [], brush='#6750A4', size=8)
        self.plot_scatter_loss = pg.ScatterPlotItem([], [], symbol='x', pen='r', size=9)
        self.chart.addItem(self.plot_scatter_success)
        self.chart.addItem(self.plot_scatter_loss)

        layout.addLayout(controls_layout)
        layout.addWidget(self.btn)
        layout.addLayout(result_layout)
        layout.addWidget(self.stats_frame)
        layout.addWidget(self.status_frame)
        layout.addLayout(view_controls_layout)
        layout.addWidget(self.chart, 1)


class Ui_TableTab(object):
    def setupUi(self, TableTab):
        TableTab.setStyleSheet("background-color: #FDFBFF;")
        layout = QVBoxLayout(TableTab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        button_layout = QHBoxLayout()

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setIcon(qta.icon("mdi.content-copy", color="#49454F"))
        self.copy_btn.setFont(QFont("Segoe UI Semibold", 10))

        self.toggle_btn = QPushButton("Start Ping")
        self.toggle_btn.setIcon(qta.icon("mdi.play", color="white"))
        self.toggle_btn.setFont(QFont("Segoe UI Semibold", 10))

        self.export_btn = QPushButton("Export")
        self.export_btn.setIcon(qta.icon("mdi.file-export-outline", color="#49454F"))
        self.export_btn.setFont(QFont("Segoe UI Semibold", 10))

        button_layout.addWidget(self.copy_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.toggle_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.export_btn)

        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #F7F2FA; color: #1D192B; border: 1px solid #CAC4D0;
                border-radius: 12px; padding: 6px 12px;
            }
            QPushButton:hover { background-color: #E8DEF8; }
        """)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #F7F2FA; color: #1D192B; border: 1px solid #CAC4D0;
                border-radius: 12px; padding: 6px 12px;
            }
            QPushButton:hover { background-color: #E8DEF8; }
        """)
        # Стиль кнопки toggle_btn буде встановлено в логіці

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["#", "Time", "Host", "Status", "Delay (ms)"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setFont(QFont("Segoe UI", 10))

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                gridline-color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #F3EDF7;
                color: #49454F;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #CAC4D0;
                font-weight: 500;
            }
            QTableWidget::item:selected {
                background-color: #EADDFF;
                color: #21005D;
            }
        """)

        layout.addLayout(button_layout)
        layout.addWidget(self.table)


class Ui_IPTestTab(object):
    def setupUi(self, IPTestTab):
        IPTestTab.setStyleSheet("background-color: #FDFBFF;")

        layout = QVBoxLayout(IPTestTab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # --- Input field and Add button ---
        input_layout = QHBoxLayout()
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Enter a domain or IP")
        self.host_input.setFont(QFont("Segoe UI", 11))
        self.host_input.setClearButtonEnabled(True)
        self.host_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 2px solid #CAC4D0;
                border-radius: 12px;
                padding: 6px;
                color: #1C1B1F;
            }
            QLineEdit:focus { border: 2px solid #6750A4; }
        """)

        self.add_btn = QPushButton()
        self.add_btn.setIcon(qta.icon("fa5s.plus", color="#6750A4"))
        self.add_btn.setToolTip("Add address to the table")
        self.add_btn.setStyleSheet("QPushButton { border: none; background: transparent; }")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        input_layout.addWidget(self.host_input)
        input_layout.addWidget(self.add_btn)

        # --- *** ПОЧАТОК ЗМІНИ ЛЕЙАУТУ КНОПОК *** ---

        # Створюємо вертикальний лейаут для ДВОХ рядів кнопок
        main_button_layout = QVBoxLayout()
        main_button_layout.setSpacing(8)  # Відстань між рядами
        main_button_layout.setContentsMargins(0, 0, 0, 0)

        button_row_1 = QHBoxLayout()
        button_row_2 = QHBoxLayout()
        button_row_1.setSpacing(15)
        button_row_2.setSpacing(15)

        btn_font = QFont("Segoe UI Semibold", 10)

        # --- Общий стиль для обычных кнопок ---
        normal_btn_style = """
            QPushButton {
                background-color: #F7F2FA;
                color: #1D192B;
                border: 1px solid #CAC4D0;
                border-radius: 12px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #E8DEF8;
            }
        """

        self.import_btn = QPushButton(" Import")
        self.import_btn.setIcon(qta.icon("fa5s.file-import", color="#49454F"))
        self.import_btn.setFont(btn_font)
        self.import_btn.setStyleSheet(normal_btn_style)

        # --- *** ПОВЕРНУЛИ ТЕКСТ *** ---
        self.copy_btn = QPushButton(" Copy")
        self.copy_btn.setIcon(qta.icon("mdi.content-copy", color="#49454F"))
        self.copy_btn.setFont(btn_font)
        self.copy_btn.setStyleSheet(normal_btn_style)
        # --- *** КІНЕЦЬ ЗМІН *** ---

        # --- *** ПОВЕРНУЛИ ТЕКСТ *** ---
        self.delete_btn = QPushButton(" Delete")
        self.delete_btn.setIcon(qta.icon("fa5s.trash-alt", color="#49454F"))
        self.delete_btn.setFont(btn_font)
        self.delete_btn.setStyleSheet(normal_btn_style)
        # --- *** КІНЕЦЬ ЗМІН *** ---

        self.start_btn = QPushButton(" Start Test")
        self.start_btn.setIcon(qta.icon("fa5s.play", color="white"))
        self.start_btn.setFont(btn_font)
        # Стиль буде встановлено в логіці

        self.export_btn = QPushButton(" Export")
        self.export_btn.setIcon(qta.icon("fa5s.file-export", color="#49454F"))
        self.export_btn.setFont(btn_font)
        self.export_btn.setStyleSheet(normal_btn_style)

        # --- Додаємо кнопки в лейаути по рядах ---

        # Ряд 1: Import, Export
        button_row_1.addWidget(self.import_btn)
        button_row_1.addWidget(self.export_btn)

        # Ряд 2: Copy, Delete, Start
        button_row_2.addWidget(self.copy_btn)
        button_row_2.addWidget(self.delete_btn)
        button_row_2.addWidget(self.start_btn)

        # Додаємо ряди до головного вертикального лейауту кнопок
        main_button_layout.addLayout(button_row_1)
        main_button_layout.addLayout(button_row_2)

        # --- *** КІНЕЦЬ ЗМІНИ ЛЕЙАУТУ КНОПОК *** ---

        # --- Table setup ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Host", "Status", "Latency (ms)", "Loss (%)"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setFont(QFont("Segoe UI", 10))
        self.table.setSortingEnabled(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                gridline-color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #F3EDF7;
                color: #49454F;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #CAC4D0;
                font-weight: 500;
            }
            QTableWidget::item:selected {
                background-color: #EADDFF;
                color: #21005D;
            }
        """)

        layout.addLayout(input_layout)
        layout.addLayout(main_button_layout)  # <-- Додаємо новий лейаут з 2-ма рядами
        layout.addWidget(self.table)
        self.table.sortByColumn(2, Qt.SortOrder.AscendingOrder)


class Ui_CustomNavBar(object):
    def setupUi(self, CustomNavBar):
        CustomNavBar.setStyleSheet("background-color: #F3EDF7;")
        CustomNavBar.setMinimumHeight(60)

        # Створюємо групу кнопок, щоб одночасно могла бути обрана лише одна
        self.button_group = QButtonGroup(CustomNavBar)
        self.button_group.setExclusive(True)

        # Головний горизонтальний лейаут
        layout = QHBoxLayout(CustomNavBar)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)

        # Створюємо кнопки навігації
        self.ping_btn = self._create_nav_button("Ping", "mdi.pulse")
        self.history_btn = self._create_nav_button("History", "mdi.history")
        self.ip_test_btn = self._create_nav_button("IP Test", "mdi.ip-network-outline")

        # Додаємо кнопки до лейауту
        layout.addWidget(self.ping_btn)
        layout.addWidget(self.history_btn)
        layout.addWidget(self.ip_test_btn)

        # Додаємо кнопки до групи з відповідними індексами
        self.button_group.addButton(self.ping_btn, 0)
        self.button_group.addButton(self.history_btn, 1)
        self.button_group.addButton(self.ip_test_btn, 2)

        # Встановлюємо початковий активний стан для першої кнопки
        self.ping_btn.setChecked(True)

    def _create_nav_button(self, text, icon_name):
        """Допоміжна функція для створення та стилізації кнопок."""
        button = QPushButton(f" {text}")

        # Налаштовуємо іконки для активного та неактивного стану
        icon = qta.icon(icon_name, color="#49454F", color_active="#1D192B")
        button.setIcon(icon)
        button.setIconSize(QSize(24, 24))
        button.setCheckable(True)
        button.setFont(QFont("Segoe UI Semibold", 10))

        # Задаємо стилі, що відповідають дизайну програми
        button.setStyleSheet("""
            QPushButton {
                color: #49454F;
                background-color: transparent;
                border: none;
                padding: 8px 12px;
                border-radius: 18px; /* Округлення для "pill" ефекту */
            }
            QPushButton:checked {
                color: #1D192B;
                background-color: #E8DEF8; /* Фон для активної кнопки */
            }
            QPushButton:hover:!checked {
                 background-color: #EADDFF; /* Фон при наведенні */
            }
        """)
        return button