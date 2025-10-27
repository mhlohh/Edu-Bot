import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

# load local .env for development only (ignored by git)
load_dotenv()

# basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("college_chatbot")

# config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # do NOT send this to client
FLASK_SECRET = os.getenv("FLASK_SECRET", "dev-secret-please-change")

# app
app = Flask(__name__)
app.secret_key = FLASK_SECRET

# data files
BASE_DIR = Path(__file__).parent
COLLEGES_FILE = BASE_DIR / "data" / "colleges.json"
FAQ_FILE = BASE_DIR / "data" / "faq.json"

def _load_json(path: Path):
    if not path.exists():
        logger.warning("Missing data file: %s", path)
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.exception("Failed to load JSON %s: %s", path, e)
        return []

# preload data (safe to re-load on demand if large)
colleges = _load_json(COLLEGES_FILE)
faqs = _load_json(FAQ_FILE)

@app.route("/")
def index():
    return render_template("index.html", colleges=colleges[:20])

@app.route("/faq")
def faq():
    # ensure faqs is a list of dicts with 'question'/'answer' or 'q'/'a'
    normalized = []
    for item in faqs:
        q = item.get("q") or item.get("question") or "Question"
        a = item.get("a") or item.get("answer") or "Answer not available."
        normalized.append({"q": q, "a": a})
    return render_template("faq.html", faqs=normalized)

@app.route("/health")
def health():
    return jsonify({"ok": True, "gemini_configured": bool(GEMINI_API_KEY)})

# example endpoint that would call your AI layer server-side (placeholder)
@app.route("/api/query", methods=["POST"])
def api_query():
    data = request.json or {}
    query = data.get("q", "").strip()
    if not query:
        return jsonify({"error": "empty query"}), 400

    # Do server-side AI call here using GEMINI_API_KEY (never expose key to client)
    # Example placeholder response:
    resp = {"answer": f"Received: {query}", "source": "stub"}
    return jsonify(resp)

if __name__ == "__main__":
    # dev server only
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
