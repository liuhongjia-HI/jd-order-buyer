import sys
import threading
import time
import random
from PySide6.QtWidgets import (QApplication, QDialog, QWidget, QVBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QHBoxLayout, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

class LoginWindow(QDialog):
    login_success = Signal() # Signal to emit when login is successful
    login_result = Signal(bool, str) # (success, message)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("系统启动 - JD Order Scraper")
        self.setFixedSize(400, 560)
        self.setWindowFlags(Qt.FramelessWindowHint) # Custom frame
        self.setAttribute(Qt.WA_TranslucentBackground) # Transparent for rounded corners
        
        self.setup_ui()
        self.setup_styles()
        self.login_result.connect(self._on_login_result)
        self.login_result.connect(self._on_login_result)
        self._logging_in = False
        
        # Dragging state
        self._is_dragging = False
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            event.accept()

    def setup_ui(self):
        # Main Container (Rounded, Dark Blue)
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setGeometry(0, 0, 400, 560)
        
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Close Button (Absolute positioning for Top-Right)
        self.close_btn = QPushButton("×", self.main_frame)
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setGeometry(350, 15, 30, 30) # Top-Right inside frame
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.reject) 

        # Title
        self.title_label = QLabel("系统登录")
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        self.subtitle_label = QLabel("请验证身份以继续")
        self.subtitle_label.setObjectName("SubtitleLabel")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.subtitle_label)
        
        layout.addSpacing(20)

        # Tabs (Visual only for now)
        tab_layout = QHBoxLayout()
        self.tab_login = QLabel("账号登录")
        self.tab_login.setObjectName("TabActive")
        self.tab_login.setAlignment(Qt.AlignCenter)
        
        self.tab_register = QLabel("新商户注册")
        self.tab_register.setObjectName("TabInactive")
        self.tab_register.setAlignment(Qt.AlignCenter)
        
        tab_layout.addWidget(self.tab_login)
        tab_layout.addWidget(self.tab_register)
        layout.addLayout(tab_layout)
        
        # Underline for active tab
        line = QFrame()
        line.setObjectName("TabLine")
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line)

        layout.addSpacing(20)

        # Inputs
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("用户名 / 手机号")
        self.user_input.setObjectName("InputBox")
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("密码")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setObjectName("InputBox")
        layout.addWidget(self.pass_input)
        
        # Forgot Password
        forgot_layout = QHBoxLayout()
        forgot_layout.addStretch()
        self.forgot_btn = QLabel("忘记密码?")
        self.forgot_btn.setObjectName("ForgotLabel")
        forgot_layout.addWidget(self.forgot_btn)
        layout.addLayout(forgot_layout)

        layout.addSpacing(20)
        
        # Login Button
        self.login_btn = QPushButton("立即登录")
        self.login_btn.setObjectName("LoginBtn")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)
        
        layout.addStretch()
        
        # Footer
        self.footer_label = QLabel("SECURE TERMINAL ACCESS v2.1")
        self.footer_label.setObjectName("FooterLabel")
        self.footer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.footer_label)

    def setup_styles(self):
        # QSS Stylesheet
        self.setStyleSheet("""
            #MainFrame {
                background-color: #0f1623;
                border-radius: 20px;
                border: 1px solid #1e2636;
            }
            #TitleLabel {
                font-size: 28px;
                font-weight: bold;
                color: #ffffff;
                font-family: "PingFang SC", "Microsoft YaHei";
            }
            #SubtitleLabel {
                font-size: 14px;
                color: #6c7589;
            }
            #TabActive {
                font-size: 16px;
                color: #64ffda;
                padding-bottom: 5px;
                border-bottom: 2px solid #64ffda;
            }
            #TabInactive {
                font-size: 16px;
                color: #6c7589;
                padding-bottom: 5px;
            }
            #TabLine {
                color: #1e2636;
            }
            #InputBox {
                background-color: #1a2233;
                border: 1px solid #2d3b50;
                border-radius: 8px;
                padding: 12px;
                color: #ffffff;
                font-size: 14px;
            }
            #InputBox:focus {
                border: 1px solid #64ffda;
            }
            #ForgotLabel {
                color: #64ffda;
                font-size: 12px;
            }
            #LoginBtn {
                background-color: #64ffda;
                color: #0a192f;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            #LoginBtn:hover {
                background-color: #4cd6b3;
            }
            #FooterLabel {
                color: #2d3b50;
                font-size: 10px;
                letter-spacing: 2px;
            }
            #CloseBtn {
                background-color: transparent;
                color: #6c7589;
                font-size: 24px;
                font-weight: 300;
                border: none;
                border-radius: 15px;
            }
            #CloseBtn:hover {
                background-color: #ff4d4f;
                color: #ffffff;
            }
        """)

    def handle_login(self):
        if self._logging_in:
            return
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()

        # 进入“模拟接口调用”状态
        self._logging_in = True
        self._set_inputs_enabled(False)
        self.subtitle_label.setText("正在校验，请稍候…")
        self.subtitle_label.setStyleSheet("color: #6c7589;")
        self.user_input.setStyleSheet("")  # reset to default style
        self.pass_input.setStyleSheet("")

        # 启动后台线程模拟接口调用（避免 UI 卡顿）
        threading.Thread(
            target=self._simulate_api_call,
            args=(username, password),
            daemon=True
        ).start()

    def _simulate_api_call(self, username: str, password: str):
        """
        模拟接口请求/耗时校验：
        - 加入随机延迟，模拟网络时间
        - 仅 admin/admin 视为通过（可替换为真实接口调用）
        """
        time.sleep(random.uniform(0.8, 1.6))
        if username == "admin" and password == "admin":
            self.login_result.emit(True, "认证通过")
        else:
            msg = "用户名或密码错误"
            self.login_result.emit(False, msg)

    def _on_login_result(self, success: bool, message: str = ""):
        self._logging_in = False
        self._set_inputs_enabled(True)

        if success:
            self.subtitle_label.setText("登录成功，正在启动...")
            self.subtitle_label.setStyleSheet("color: #64ffda;")
            print("Login Successful")
            self.accept()
            self.login_success.emit()
        else:
            print("Login Failed")
            self.subtitle_label.setText(message or "登录失败")
            self.subtitle_label.setStyleSheet("color: #ff4d4f;")
            self.user_input.setStyleSheet("border: 1px solid #ff4d4f; background-color: #1a2233; color: #ffffff;")
            self.pass_input.setStyleSheet("border: 1px solid #ff4d4f; background-color: #1a2233; color: #ffffff;")

    def _set_inputs_enabled(self, enabled: bool):
        self.user_input.setEnabled(enabled)
        self.pass_input.setEnabled(enabled)
        self.login_btn.setEnabled(enabled)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
