import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from ai.chatbot import get_chat_response

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

# preload data
colleges = _load_json(COLLEGES_FILE)
faqs = _load_json(FAQ_FILE)

# map the index view to the endpoint name "home" (templates expect url_for('home'))
@app.route("/", endpoint="home")
def index():
    return render_template("index.html", colleges=colleges[:20])

@app.route("/faq")
def faq():
    normalized = []
    for item in faqs:
        if not isinstance(item, dict):
            continue
        q = item.get("q") or item.get("question") or "Question"
        a = item.get("a") or item.get("answer") or "Answer not available."
        normalized.append({"q": q, "a": a})
    return render_template("faq.html", faqs=normalized)

@app.route("/health")
def health():
    return jsonify({"ok": True, "gemini_configured": bool(GEMINI_API_KEY)})

@app.route("/api/query", methods=["POST"])
def api_query():
    data = request.json or {}
    query = data.get("q", "").strip()
    if not query:
        return jsonify({"error": "empty query"}), 400
    answer = get_chat_response(query)
    return jsonify({"answer": answer, "source": "gemini"})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    message = data.get("message", "").strip()
    language = data.get("language", "en")
    if not message:
        return jsonify({"error": "empty message"}), 400
    response = get_chat_response(message, language)
    return jsonify({"response": response})

@app.route("/colleges", endpoint="colleges_page")
def colleges_page():
    # pass the colleges list (adjust slicing/filters as needed)
    return render_template("colleges.html", colleges=colleges)

@app.route("/about", endpoint="about")
def about():
    return render_template("about.html")

@app.route("/contact", endpoint="contact")
def contact():
    return render_template("contact.html")

@app.route("/contact/send", endpoint="send_message", methods=["POST"])
def send_message():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()
    logger.info("Contact form: name=%s email=%s", name, email)
    flash(f"Thanks {name}! Your message has been received.", "success")
    return redirect(url_for("contact"))

@app.route("/courses", endpoint="courses")
def courses():
    return render_template("courses.html")

@app.route("/admin/login", endpoint="admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == os.getenv("ADMIN_PASSWORD", "admin"):
            from flask import session
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid password", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout", endpoint="admin_logout")
def admin_logout():
    from flask import session
    session.pop("admin_logged_in", None)
    return redirect(url_for("home"))

@app.route("/admin/dashboard", endpoint="admin_dashboard")
def admin_dashboard():
    from flask import session
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    return render_template("admin_dashboard.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
