import os
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
SECRET = os.getenv("SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"[DEBUG] GEMINI_API_KEY loaded: {bool(GEMINI_API_KEY)}")
