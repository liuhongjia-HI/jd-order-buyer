import sys
from PySide6.QtWidgets import QApplication
from core.scraper import JDScraper
from gui.login import LoginWindow
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    login_window = LoginWindow()
    if login_window.exec():
        scraper = JDScraper(headless=False)
        window = MainWindow(scraper)
        window.show()
        sys.exit(app.exec())

    sys.exit(0)


if __name__ == "__main__":
    main()
