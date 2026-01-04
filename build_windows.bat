@echo off
setlocal

rem === Config ===
set "APP_NAME=jd-order-export"
set "VENV_DIR=.venv"
set "PYTHON_EXE=D:\Programs\Python\Python313\python.exe"

rem If the pinned Python path doesn't exist, fall back to py -3 or python.
if not exist "%PYTHON_EXE%" (
    where py >nul 2>nul
    if errorlevel 1 (
        set "PYTHON_EXE=python"
        set "PYTHON_ARGS="
    ) else (
        set "PYTHON_EXE=py"
        set "PYTHON_ARGS=-3"
    )
) else (
    set "PYTHON_ARGS="
)

echo [1/5] Preparing venv...
if not exist "%VENV_DIR%\Scripts\python.exe" (
    "%PYTHON_EXE%" %PYTHON_ARGS% -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"

echo [2/5] Installing deps...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
"%VENV_DIR%\Scripts\python.exe" -m pip install pyinstaller

echo [3/5] Installing Playwright chromium...
"%VENV_DIR%\Scripts\python.exe" -m playwright install chromium

rem Ensure data dirs exist
if not exist "downloads" mkdir "downloads"

echo [4/5] Building...
"%VENV_DIR%\Scripts\python.exe" -m PyInstaller --onefile --noconsole --name "%APP_NAME%" --collect-all playwright --collect-all playwright_stealth --collect-all PySide6 main.py

echo [5/5] Done. Output: dist\%APP_NAME%.exe
endlocal

