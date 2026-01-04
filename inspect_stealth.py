import playwright_stealth
print("Attributes:", dir(playwright_stealth))
try:
    from playwright_stealth import stealth_sync
    print("stealth_sync imported successfully")
except ImportError as e:
    print(f"Import failed: {e}")
