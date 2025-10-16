import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
SECRET = os.getenv("SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
