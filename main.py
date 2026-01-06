import sys
from PySide6.QtWidgets import QApplication
from core.scraper import JDScraper
from gui.login import LoginWindow
from gui.main_window import MainWindow


def main():
    try:
        app = QApplication(sys.argv)

        login_window = LoginWindow()
        if login_window.exec():
            scraper = JDScraper(headless=False)
            window = MainWindow(scraper)
            window.show()
            sys.exit(app.exec())
        else:
            sys.exit(0)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Critical Application Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
