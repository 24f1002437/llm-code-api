# app.py
from flask import Flask, request, jsonify
import threading
import os, shutil, json
from llm_generator import generate_app
from github_deploy import deploy_to_github
from utils import verify_secret, post_with_retry
from config import GITHUB_USERNAME, GITHUB_TOKEN, SECRET, GEMINI_API_KEY

# ----------------------------
# CONFIG
# ----------------------------
USE_MOCK = False  # True = local mock, False = Gemini API

# ----------------------------
# FLASK APP
# ----------------------------
app = Flask(__name__)

# ----------------------------
# RESULTS STORAGE
# ----------------------------
results_db = []
RESULTS_FILE = "results_db.json"
results_lock = threading.Lock()

# ----------------------------
# BACKGROUND TASK
# ----------------------------
def process_task(data):
    repo_name = data["task"]
    output_dir = f"temp/{repo_name}"
    os.makedirs(output_dir, exist_ok=True)

    try:
        # 1. Generate app using LLM
        generate_app(data.get("brief", ""), data.get("attachments", []), output_dir, use_mock=USE_MOCK)

        # 2. Deploy to GitHub
        repo_url, commit_sha, pages_url = deploy_to_github(output_dir, repo_name, token=GITHUB_TOKEN)

        # 3. Notify evaluation server with retries
        payload = {
            "email": data.get("email"),
            "task": data.get("task"),
            "round": data.get("round"),
            "nonce": data.get("nonce"),
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "pages_url": pages_url
        }
        post_with_retry(data.get("evaluation_url"), payload)
    finally:
        # 4. Cleanup temp directory
        shutil.rmtree(output_dir, ignore_errors=True)

# ----------------------------
# ROUTES
# ----------------------------
@app.route("/build_app", methods=["POST"])
def build_app():
    data = request.get_json()
    if not data or not verify_secret(data.get("secret")):
        return jsonify({"status": "error", "message": "Invalid secret"}), 400

    threading.Thread(target=process_task, args=(data,)).start()
    return jsonify({"status": "ok"})  # HTTP 200 immediately

@app.route("/revise_app", methods=["POST"])
def revise_app():
    data = request.get_json()
    if not data or not verify_secret(data.get("secret")):
        return jsonify({"status": "error", "message": "Invalid secret"}), 400

    threading.Thread(target=process_task, args=(data,)).start()
    return jsonify({"status": "ok"})  # HTTP 200 immediately

@app.route("/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    # Thread-safe append
    with results_lock:
        results_db.append(data)
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, "r") as f:
                existing = json.load(f)
        else:
            existing = []

        existing.append(data)
        with open(RESULTS_FILE, "w") as f:
            json.dump(existing, f, indent=2)

    print(f"[EVALUATE] Received: {json.dumps(data)}")
    return jsonify({"status": "ok"})

# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
