
import sys
from PySide6.QtWidgets import QApplication
from gui.login import LoginWindow

def test_login():
    print("DEBUG: Creating QApplication")
    app = QApplication(sys.argv)
    
    print("DEBUG: Creating LoginWindow")
    try:
        window = LoginWindow()
        print("DEBUG: LoginWindow created. calling show()")
        window.show()
        print("DEBUG: LoginWindow shown. calling exec()")
        res = window.exec()
        print(f"DEBUG: LoginWindow.exec() returned {res}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"DEBUG: Exception: {e}")

if __name__ == "__main__":
    test_login()
