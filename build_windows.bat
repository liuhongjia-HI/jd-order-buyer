@echo off
setlocal

rem === 配置 ===
set APP_NAME=京东订单导出
set VENV_DIR=.venv

echo [1/5] 准备虚拟环境...
if not exist "%VENV_DIR%\Scripts\python.exe" (
    python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"

echo [2/5] 安装依赖...
pip install --upgrade pip >nul
pip install -r requirements.txt >nul
pip install pyinstaller >nul

echo [3/5] 安装 Playwright 浏览器 (chromium)...
python -m playwright install chromium

echo [4/5] 开始打包...
pyinstaller ^
  --onefile ^
  --noconsole ^
  --name "%APP_NAME%" ^
  --add-data "static;static" ^
  --add-data "downloads;downloads" ^
  desktop_main.py

echo [5/5] 完成。可执行文件位于: dist\%APP_NAME%.exe
endlocal
