import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QObject, Signal, QThread, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QPlainTextEdit,
    QListWidget,
    QListWidgetItem,
    QFormLayout,
    QMessageBox,
    QFrame,
    QStackedWidget,
)


class TaskWorker(QObject):
    finished = Signal(object, object)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._func(*self._args, **self._kwargs)
            self.finished.emit(result, None)
        except Exception as exc:
            self.finished.emit(None, exc)


class MainWindow(QWidget):
    def __init__(self, scraper):
        super().__init__()
        self.scraper = scraper
        self.download_dir = Path(scraper.download_dir)
        self.auth_path = Path(scraper.auth_file)
        self._latest_file = None
        self._busy = False
        self._worker_thread = None
        self._worker = None

        self.setObjectName("appRoot")
        self.setWindowTitle("JDTools 控制台")
        self.resize(1200, 760)

        self._build_ui()
        self._apply_styles()
        self._refresh_auth_status()
        self.refresh_downloads()
        self.switch_view("console")

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(12)

        logo_row = QHBoxLayout()
        logo_text = QLabel("JDTools")
        logo_text.setObjectName("logoText")
        logo_row.addWidget(logo_text)
        logo_row.addStretch()
        sidebar_layout.addLayout(logo_row)

        self.auth_label = QLabel("登录状态: 未检测")
        self.auth_label.setObjectName("authLabel")
        sidebar_layout.addWidget(self.auth_label)

        self.nav_console = QPushButton("控制台 / Console")
        self.nav_console.setProperty("nav", True)
        self.nav_console.clicked.connect(lambda: self.switch_view("console"))
        self.nav_data = QPushButton("数据预览 / Data")
        self.nav_data.setProperty("nav", True)
        self.nav_data.clicked.connect(lambda: self.switch_view("data"))
        sidebar_layout.addWidget(self.nav_console)
        sidebar_layout.addWidget(self.nav_data)

        sidebar_layout.addStretch()

        self.settings_label = QLabel("设置 / Settings")
        self.settings_label.setObjectName("settingsLabel")
        sidebar_layout.addWidget(self.settings_label)

        self.account_btn = QPushButton("切换京东账号")
        self.account_btn.setObjectName("accountBtn")
        self.account_btn.clicked.connect(self.start_login)
        sidebar_layout.addWidget(self.account_btn)

        root.addWidget(self.sidebar)

        self.main_content = QWidget()
        self.main_content.setObjectName("mainContent")
        main_layout = QVBoxLayout(self.main_content)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(0)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        root.addWidget(self.main_content, 1)

        self.console_view = QWidget()
        self.data_view = QWidget()
        self.stack.addWidget(self.console_view)
        self.stack.addWidget(self.data_view)

        self._build_console_view()
        self._build_data_view()

    def _build_console_view(self):
        layout = QVBoxLayout(self.console_view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        status_row = QHBoxLayout()
        status_row.setSpacing(20)

        status_card = self._build_card("状态", "就绪", "statusValue")
        count_card = self._build_card("已捕获订单", "0", "countValue")

        status_row.addWidget(status_card)
        status_row.addWidget(count_card)
        layout.addLayout(status_row)

        self.log_box = QPlainTextEdit()
        self.log_box.setObjectName("consoleBox")
        self.log_box.setReadOnly(True)
        self.log_box.appendPlainText("[系统] 等待指令...")
        layout.addWidget(self.log_box, 1)

        action_row = QHBoxLayout()
        action_row.addStretch()
        action_row.addWidget(QLabel("时间范围:"))

        self.range_combo = QComboBox()
        self.range_combo.setObjectName("rangeCombo")
        self._init_range_options()
        action_row.addWidget(self.range_combo)

        self.start_btn = QPushButton("开始采集")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.start_scrape)
        action_row.addWidget(self.start_btn)

        layout.addLayout(action_row)

    def _build_data_view(self):
        layout = QVBoxLayout(self.data_view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        data_card = QFrame()
        data_card.setObjectName("dataCard")
        data_layout = QVBoxLayout(data_card)
        data_layout.setContentsMargins(20, 20, 20, 20)
        data_layout.setSpacing(16)

        header_row = QHBoxLayout()
        title_col = QVBoxLayout()

        title = QLabel("数据中心（最近一次采集）")
        title.setObjectName("dataTitle")
        subtitle = QLabel("最新导出文件信息")
        subtitle.setObjectName("dataSubtitle")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        header_row.addLayout(title_col)
        header_row.addStretch()

        self.open_downloads_btn = QPushButton("打开下载目录")
        self.open_downloads_btn.setObjectName("btnSecondary")
        self.open_downloads_btn.clicked.connect(self.open_downloads_folder)
        self.open_latest_btn = QPushButton("打开最新文件")
        self.open_latest_btn.setObjectName("btnPrimary")
        self.open_latest_btn.clicked.connect(self.open_latest_file)
        self.open_latest_btn.setEnabled(False)

        header_row.addWidget(self.open_downloads_btn)
        header_row.addWidget(self.open_latest_btn)

        data_layout.addLayout(header_row)

        meta_layout = QFormLayout()
        meta_layout.setLabelAlignment(Qt.AlignLeft)
        meta_layout.setFormAlignment(Qt.AlignTop)

        self.latest_name = QLabel("-")
        self.latest_time = QLabel("-")
        self.latest_size = QLabel("-")
        self.latest_path = QLabel("-")
        for lbl in (self.latest_name, self.latest_time, self.latest_size, self.latest_path):
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lbl.setWordWrap(True)

        meta_layout.addRow(self._meta_key("最新文件:"), self.latest_name)
        meta_layout.addRow(self._meta_key("生成时间:"), self.latest_time)
        meta_layout.addRow(self._meta_key("大小:"), self.latest_size)
        meta_layout.addRow(self._meta_key("保存路径:"), self.latest_path)

        data_layout.addLayout(meta_layout)
        layout.addWidget(data_card)

        list_card = QFrame()
        list_card.setObjectName("dataCard")
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(20, 20, 20, 20)
        list_layout.setSpacing(12)

        list_title = QLabel("下载列表")
        list_title.setObjectName("dataTitle")
        list_layout.addWidget(list_title)

        self.download_list = QListWidget()
        self.download_list.setObjectName("downloadList")
        self.download_list.itemDoubleClicked.connect(self.open_selected_file)
        list_layout.addWidget(self.download_list, 1)

        layout.addWidget(list_card, 1)

    def _build_card(self, title: str, value: str, value_object: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)

        label = QLabel(title)
        label.setObjectName("cardLabel")
        value_label = QLabel(value)
        value_label.setObjectName(value_object)

        card_layout.addWidget(label)
        card_layout.addWidget(value_label)

        if value_object == "statusValue":
            self.status_label = value_label
        elif value_object == "countValue":
            self.count_label = value_label

        return card

    def _meta_key(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setProperty("metaKey", True)
        return label

    def _apply_styles(self):
        self.setStyleSheet(
            """
            * {
                outline: none;
            }
            #appRoot {
                background-color: #0d1117;
                color: #c9d1d9;
                font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
                font-size: 14px;
            }
            QLabel {
                color: #c9d1d9;
            }
            QWidget#sidebar {
                background-color: #161b22;
                border-right: 1px solid #30363d;
            }
            QLabel#logoText {
                font-size: 24px;
                font-weight: 700;
                color: #58a6ff;
                padding-left: 8px;
            }
            QLabel#authLabel {
                color: #8b949e;
                font-size: 13px;
                padding-left: 8px;
            }
            QPushButton[nav="true"] {
                text-align: left;
                padding: 12px 16px;
                border-radius: 6px;
                border: none;
                color: #8b949e;
                background: transparent;
                font-weight: 500;
                margin: 0 8px;
            }
            QPushButton[nav="true"]:hover {
                background-color: #21262d;
                color: #c9d1d9;
            }
            QPushButton[nav="true"][active="true"] {
                background-color: #1f6feb;
                color: #ffffff;
                font-weight: 600;
            }
            QLabel#settingsLabel {
                color: #8b949e;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QPushButton#accountBtn {
                border: 1px solid #30363d;
                color: #c9d1d9;
                border-radius: 6px;
                padding: 10px;
                background: #21262d;
                margin: 0 8px;
                font-weight: 500;
            }
            QPushButton#accountBtn:hover {
                background-color: #30363d;
                border-color: #8b949e;
            }
            QFrame#card, QFrame#dataCard {
                background-color: #161b22;
                border-radius: 12px;
                border: 1px solid #30363d;
            }
            QLabel#cardLabel {
                color: #8b949e;
                font-size: 14px;
                font-weight: 500;
            }
            QLabel#statusValue {
                font-size: 32px;
                font-weight: 700;
                color: #58a6ff;
            }
            QLabel#countValue {
                font-size: 32px;
                font-weight: 700;
                color: #3fb950;
            }
            QPlainTextEdit#consoleBox {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 12px;
                padding: 12px;
                font-family: Consolas, "Courier New", monospace;
                font-size: 13px;
                line-height: 1.4;
            }
            QComboBox#rangeCombo {
                background-color: #161b22;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 160px;
            }
            QComboBox#rangeCombo:hover {
                border-color: #58a6ff;
            }
            QComboBox#rangeCombo::drop-down {
                border: none;
            }
            QComboBox#rangeCombo QAbstractItemView {
                background-color: #161b22;
                color: #c9d1d9;
                selection-background-color: #1f6feb;
                selection-color: #ffffff;
                outline: none;
                border: 1px solid #30363d;
            }
            QPushButton#startBtn {
                background-color: #238636;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton#startBtn:hover {
                background-color: #2ea043;
            }
            QPushButton#startBtn:disabled {
                background-color: #21262d;
                color: #484f58;
            }
            QLabel#dataTitle {
                font-size: 18px;
                font-weight: 600;
                color: #c9d1d9;
            }
            QLabel#dataSubtitle {
                color: #8b949e;
                font-size: 13px;
            }
            QLabel[metaKey="true"] {
                color: #8b949e;
                font-weight: 500;
            }
            QPushButton#btnPrimary {
                background-color: #1f6feb;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 500;
            }
            QPushButton#btnPrimary:hover {
                background-color: #388bfd;
            }
            QPushButton#btnSecondary {
                background-color: transparent;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 500;
            }
            QPushButton#btnSecondary:hover {
                background-color: #21262d;
                border-color: #8b949e;
            }
            QListWidget#downloadList {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget#downloadList::item {
                padding: 8px 12px;
                border-radius: 6px;
                margin-bottom: 2px;
            }
            QListWidget#downloadList::item:selected {
                background-color: #1f6feb;
                color: #ffffff;
            }
            QListWidget#downloadList::item:hover:!selected {
                background-color: #161b22;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #30363d;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #58a6ff;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )

    def _init_range_options(self):
        self.range_combo.clear()
        self.range_combo.addItem("近三个月订单", "1")
        self.range_combo.addItem("今年内订单", "2")
        current_year = datetime.now().year
        for year in range(current_year - 1, 2014, -1):
            self.range_combo.addItem(f"{year}年订单", str(year))

    def _append_log(self, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.appendPlainText(f"[{ts}] {message}")
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def _set_busy(self, busy: bool):
        self._busy = busy
        self.account_btn.setEnabled(not busy)
        self.start_btn.setEnabled(not busy)
        self.range_combo.setEnabled(not busy)
        self.open_latest_btn.setEnabled(not busy and self._latest_file is not None)
        self.open_downloads_btn.setEnabled(not busy)

    def _start_task(self, label: str, func, on_done):
        if self._busy:
            return
        self._set_busy(True)
        self._append_log(label)
        worker = TaskWorker(func)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.finished.connect(lambda result, err: self._handle_task_done(label, result, err, on_done))
        self._worker_thread = thread
        self._worker = worker
        thread.start()

    def _handle_task_done(self, label, result, err, on_done):
        self._set_busy(False)
        self._worker = None
        self._worker_thread = None
        if err is not None:
            self._append_log(f"{label}失败: {err}")
            QMessageBox.warning(self, "任务失败", str(err))
            return
        on_done(result)

    def _refresh_auth_status(self):
        if self.auth_path.exists():
            self.auth_label.setText("登录状态: 已保存 auth.json")
        else:
            self.auth_label.setText("登录状态: 未检测到 auth.json")

    def _format_size(self, size: int) -> str:
        if size is None:
            return "-"
        units = ["B", "KB", "MB", "GB"]
        value = float(size)
        idx = 0
        while value >= 1024 and idx < len(units) - 1:
            value /= 1024
            idx += 1
        return f"{value:.1f} {units[idx]}"

    def refresh_downloads(self):
        self.download_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(self.download_dir.glob("*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)

        self.download_list.clear()
        for f in files:
            item = QListWidgetItem(f.name)
            item.setData(Qt.UserRole, str(f))
            item.setToolTip(str(f))
            self.download_list.addItem(item)

        if files:
            latest = files[0]
            stat = latest.stat()
            self._latest_file = latest
            self.latest_name.setText(latest.name)
            self.latest_time.setText(datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"))
            self.latest_size.setText(self._format_size(stat.st_size))
            self.latest_path.setText(str(latest))
            self.open_latest_btn.setEnabled(not self._busy)
        else:
            self._latest_file = None
            self.latest_name.setText("-")
            self.latest_time.setText("-")
            self.latest_size.setText("-")
            self.latest_path.setText("-")
            self.open_latest_btn.setEnabled(False)

    def switch_view(self, view: str):
        if view == "data":
            self.stack.setCurrentWidget(self.data_view)
            self._set_nav_active(self.nav_data, True)
            self._set_nav_active(self.nav_console, False)
            self.refresh_downloads()
        else:
            self.stack.setCurrentWidget(self.console_view)
            self._set_nav_active(self.nav_console, True)
            self._set_nav_active(self.nav_data, False)

    def _set_nav_active(self, btn: QPushButton, active: bool):
        btn.setProperty("active", active)
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def open_latest_file(self):
        if not self._latest_file:
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._latest_file)))

    def open_selected_file(self, item: QListWidgetItem):
        path = item.data(Qt.UserRole)
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def open_downloads_folder(self):
        path = str(self.download_dir)
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        except Exception as exc:
            QMessageBox.warning(self, "打开失败", str(exc))

    def start_login(self):
        def _done(success):
            if success:
                self.status_label.setText("登录完成")
                self._append_log("登录成功，auth.json 已更新。")
            else:
                self.status_label.setText("登录失败")
                self._append_log("登录失败或已取消。")
            self._refresh_auth_status()

        self.status_label.setText("登录中")
        self._start_task("开始登录，请在弹出的浏览器完成扫码...", lambda: self.scraper.login(force_fresh=True), _done)

    def start_scrape(self):
        filter_type = self.range_combo.currentData()

        def _done(result):
            if isinstance(result, dict):
                status = result.get("status")
                if status == "success":
                    count = result.get("order_count") or result.get("count") or "-"
                    self.count_label.setText(str(count))
                    self.status_label.setText("完成")
                    self._append_log("采集完成。")
                elif status == "empty":
                    self.status_label.setText("无数据")
                    self._append_log("未找到订单数据。")
                else:
                    self.status_label.setText("失败")
                    self._append_log(f"采集失败: {result.get('message')}")
            else:
                self.status_label.setText("失败")
                self._append_log("采集失败: 返回结果异常")

            self.refresh_downloads()

        self.status_label.setText("采集中")
        self._start_task(f"开始采集 (Filter={filter_type})...", lambda: self.scraper.scrape_orders(filter_type), _done)
