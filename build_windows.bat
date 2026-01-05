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

"%VENV_DIR%\Scripts\python.exe" -m pip install playwright-stealth

echo [3/5] Skipping bundled browser install (using system browser)...
rem Playwright browsers will not be bundled.

rem Ensure data dirs exist
if not exist "downloads" mkdir "downloads"

echo [3.5/5] Cleaning up potential bundled browsers to save space...
if exist "%VENV_DIR%\Lib\site-packages\playwright\driver\package\.local-browsers" (
    rmdir /s /q "%VENV_DIR%\Lib\site-packages\playwright\driver\package\.local-browsers"
    echo Removed bundled browsers from venv.
)

echo [4/5] Building...
"%VENV_DIR%\Scripts\python.exe" -m PyInstaller --onefile --noconsole --name "%APP_NAME%" ^
    --hidden-import="playwright.sync_api" ^
    --hidden-import="playwright_stealth" ^
    --hidden-import="PySide6" ^
    --collect-data="playwright" ^
    --collect-all="playwright_stealth" ^
    --exclude-module="tkinter" ^
    main.py

echo [5/5] Done. Output: dist\%APP_NAME%.exe
endlocal

