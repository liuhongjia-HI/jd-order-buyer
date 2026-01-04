
from playwright.sync_api import sync_playwright
import os
import json
import time

def verify():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    auth_file = os.path.join(base_dir, "auth.json")
    
    if not os.path.exists(auth_file):
        print("ERROR: auth.json not found")
        return

    print("Starting verification (Headless)...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Visible for debug? No, headless is faster
        # Load state
        context = browser.new_context(storage_state=auth_file, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()
        
        try:
            print("Navigating to Order List...")
            page.goto("https://order.jd.com/center/list.action?d=1&s=4096", timeout=60000)
            page.wait_for_load_state("networkidle")
            
            if "passport.jd.com" in page.url:
                print("ERROR: Session expired, redirected to login.")
                return

            print("Waiting for order table (tbody[id^='tb-'] )...")
            try:
                page.wait_for_selector("tbody[id^='tb-']", timeout=10000)
                print("SUCCESS: Found order elements!")
            except Exception as e:
                print(f"FAILED to find selectors: {e}")
                # debug dump
                with open("verify_debug.html", "w") as f:
                    f.write(page.content())
                print("Dumped HTML to verify_debug.html")
                return

            rows = page.query_selector_all("tbody[id^='tb-']")
            print(f"Found {len(rows)} orders on the first page.")
            
            if len(rows) > 0:
                print("--- First Order Details ---")
                row = rows[0]
                # Try simple check
                print(f"Row ID: {row.get_attribute('id')}")
                print(f"Inner Text Snapshot: {row.inner_text()[:100]}...")
                
        except Exception as e:
            print(f"Script Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify()
