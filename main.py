from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.concurrency import run_in_threadpool
import uvicorn
import os
from pathlib import Path
import datetime
from core.scraper import JDScraper
from loguru import logger

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = Path(os.getenv("JD_LOG_DIR", BASE_DIR / "logs")).expanduser()
LOG_DIR.mkdir(parents=True, exist_ok=True)
# File日志，方便交付给客户定位问题
logger.add(
    LOG_DIR / "app.log",
    rotation="10 MB",
    retention="7 days",
    enqueue=True,
    encoding="utf-8",
    backtrace=False,
    diagnose=False,
)
AUTH_PATH = BASE_DIR / "auth.json"
DOWNLOADS_PATH = Path(os.getenv("JD_DOWNLOAD_DIR", BASE_DIR / "downloads")).expanduser().resolve()
import subprocess
import platform

app = FastAPI()

# Mount static files
os.makedirs(DOWNLOADS_PATH, exist_ok=True)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/downloads", StaticFiles(directory=DOWNLOADS_PATH), name="downloads")

# Global scraper instance
scraper = JDScraper(headless=False)

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.post("/api/login")
async def login_task(background_tasks: BackgroundTasks):
    """Trigger manual login flow"""
    def run_login():
        success = scraper.login()
        if success:
            logger.info("Login process completed successfully.")
        else:
            logger.error("Login process failed.")
            
    background_tasks.add_task(run_login)
    return {"status": "started", "message": "Opening browser for login..."}

@app.get("/api/check-auth")
async def check_auth():
    """Check if auth file exists"""
    if AUTH_PATH.exists():
        return {"authenticated": True}
    return {"authenticated": False}

@app.post("/api/scrape")
async def scrape_task(filter_type: str = "1"):
    """
    Start scraping.
    filter_type: '1' (3 months), '2' (this year), etc.
    Runs in a thread to keep the event loop free (Playwright Sync API).
    """
    try:
        result = await run_in_threadpool(scraper.scrape_orders, filter_type)
        return result
    except Exception as e:
        logger.error(f"API Scrape Error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/latest-file")
async def latest_file():
    """Return latest file metadata for data preview"""
    if not DOWNLOADS_PATH.exists():
        return {}
    files = [f for f in DOWNLOADS_PATH.iterdir() if f.suffix.lower() == ".xlsx"]
    if not files:
        return {}
    latest = max(files, key=lambda p: p.stat().st_mtime)
    stat = latest.stat()
    return {
        "name": latest.name,
        "path": f"/downloads/{latest.name}",
        "full_path": str(latest),
        "modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "size": stat.st_size
    }

@app.post("/api/open-folder")
async def open_folder():
    """Open the downloads folder in system explorer"""
    path = str(DOWNLOADS_PATH)
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", path])
        else:  # Linux
            subprocess.run(["xdg-open", path])
        return {"status": "success", "message": "Folder opened"}
    except Exception as e:
        logger.error(f"Failed to open folder: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
