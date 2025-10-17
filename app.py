# app.py
from flask import Flask, request, jsonify
import threading
import os, shutil, json
from llm_generator import generate_app
from github_deploy import deploy_to_github
from utils import verify_secret, post_with_retry
from config import GITHUB_USERNAME, GITHUB_TOKEN, SECRET, GEMINI_API_KEY

# ----------------------------
# INITIAL LOGS
# ----------------------------
print("--------------------------------------------------")
print("[INIT] Starting Flask app for LLM Code Deployment")
print(f"[INIT] GitHub Username: {GITHUB_USERNAME}")
print(f"[INIT] Secret Loaded: {'Yes' if SECRET else 'No'}")
print(f"[INIT] Gemini API Key Loaded: {'Yes' if GEMINI_API_KEY else 'No'}")
print("--------------------------------------------------")

# Auto-detect mock/live mode
USE_MOCK = not bool(GEMINI_API_KEY)
print(f"[MODE] {'MOCK' if USE_MOCK else 'LIVE (Gemini API Active)'} mode enabled.")

# ----------------------------
# FLASK APP SETUP
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
        # 1️⃣ Generate app using Gemini or mock mode
        generate_app(
            brief=data.get("brief", ""),
            attachments=data.get("attachments", []),
            output_dir=output_dir,
            use_mock=USE_MOCK
        )

        # 2️⃣ Deploy to GitHub
        repo_url, commit_sha, pages_url = deploy_to_github(
            output_dir,
            repo_name,
            token=GITHUB_TOKEN
        )

        # 3️⃣ Notify evaluation server
        payload = {
            "email": data.get("email"),
            "task": data.get("task"),
            "round": data.get("round"),
            "nonce": data.get("nonce"),
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "pages_url": pages_url
        }

        print(f"[INFO] Sending evaluation payload to {data.get('evaluation_url')}")
        post_with_retry(data.get("evaluation_url"), payload)
        print("[INFO] Evaluation notification sent successfully.")

    except Exception as e:
        print(f"[ERROR] Task processing failed: {e}")

    finally:
        # 4️⃣ Cleanup temp directory
        shutil.rmtree(output_dir, ignore_errors=True)
        print(f"[CLEANUP] Removed temp folder: {output_dir}")

# ----------------------------
# ROUTES
# ----------------------------

@app.route("/", methods=["GET"])
def home():
    """Health check route."""
    return jsonify({
        "status": "running",
        "mode": "mock" if USE_MOCK else "live",
        "github_user": GITHUB_USERNAME
    })

@app.route("/build_app", methods=["POST"])
def build_app():
    data = request.get_json()
    if not data or not verify_secret(data.get("secret")):
        return jsonify({"status": "error", "message": "Invalid secret"}), 400

    threading.Thread(target=process_task, args=(data,)).start()
    print(f"[BUILD] Started task: {data.get('task')}")
    return jsonify({"status": "ok", "message": "Build started"}), 200

@app.route("/revise_app", methods=["POST"])
def revise_app():
    data = request.get_json()
    if not data or not verify_secret(data.get("secret")):
        return jsonify({"status": "error", "message": "Invalid secret"}), 400

    threading.Thread(target=process_task, args=(data,)).start()
    print(f"[REVISE] Started revision task: {data.get('task')}")
    return jsonify({"status": "ok", "message": "Revision started"}), 200

@app.route("/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    with results_lock:
        results_db.append(data)
        existing = []
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, "r") as f:
                existing = json.load(f)
        existing.append(data)
        with open(RESULTS_FILE, "w") as f:
            json.dump(existing, f, indent=2)

    print(f"[EVALUATE] Received: {json.dumps(data)}")
    return jsonify({"status": "ok"}), 200

# ----------------------------
# MAIN ENTRY
# ----------------------------
if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    port = int(os.getenv("PORT", 5000))
    print(f"[START] Running server on port {port}")
    app.run(host="0.0.0.0", port=port)
