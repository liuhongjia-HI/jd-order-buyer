import sys
import threading
import uvicorn
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
from gui.login import LoginWindow
from main import app as fastapi_app

def run_server():
    """Run FastAPI server in a separate thread"""
    uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")

def start_main_logic():
    """Start server in background"""
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1.5)  # give uvicorn a moment
    return server_thread

def main():
    app = QApplication(sys.argv)
    
    # Show Login Window
    login_window = LoginWindow()
    
    if login_window.exec():
        # Login Successful (exec returns QDialog.Accepted)
        print("Authed. Starting application...")
        start_main_logic()

        # Embed the dashboard in a Qt WebEngine view (desktop体验)
        view = QWebEngineView()
        view.setWindowTitle("JDTools 控制台")
        view.resize(1280, 800)
        view.load(QUrl("http://127.0.0.1:8000"))
        view.show()

        sys.exit(app.exec())
    else:
        print("Login cancelled.")
        sys.exit(0)

if __name__ == "__main__":
    main()
