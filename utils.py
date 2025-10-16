# utils.py
import requests
from config import SECRET
import time

# ----------------------------
# Secret Verification
# ----------------------------
def verify_secret(secret: str) -> bool:
    """Check if the provided secret matches the one from .env/config."""
    return secret == SECRET


# ----------------------------
# POST with retry
# ----------------------------
def post_with_retry(url: str, payload: dict, retries: int = 5):
    """
    POST JSON payload to evaluation URL with exponential backoff.
    """
    if not url:
        print("[WARN] No evaluation URL provided.")
        return

    delay = 1
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                print(f"[INFO] Successfully posted to {url}")
                return
            else:
                print(f"[WARN] Attempt {attempt}: Status {resp.status_code}, retrying in {delay}s...")
        except requests.RequestException as e:
            print(f"[ERROR] Attempt {attempt}: {e}, retrying in {delay}s...")
        time.sleep(delay)
        delay *= 2  # exponential backoff
    print(f"[ERROR] Failed to POST to {url} after {retries} attempts.")
