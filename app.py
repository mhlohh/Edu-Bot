import os, json, re
from flask import Flask, render_template, request, jsonify, flash, redirect, session, url_for
from dotenv import load_dotenv
import google.generativeai as genai

# ------------------ APP SETUP ------------------ #
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "super_secret_key")

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("🔑 Gemini API Key present:", bool(GEMINI_API_KEY))

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        print("⚠️ Gemini init error:", e)
        model = None
else:
    model = None

# ------------------ DATA ------------------ #
with open("data/colleges.json", "r", encoding="utf-8") as f:
    COLLEGES = json.load(f)

# ------------------ HELPERS ------------------ #
def _norm(s):
    return re.sub(r'[^a-z0-9]+', '', (s or '').lower())

def _extract_fee_value(fee_obj):
    """Return an int fee extracted from a fee object (supports multiple key names)."""
    if fee_obj is None:
        return 0
    if isinstance(fee_obj, (int, float)):
        return int(fee_obj)
    if isinstance(fee_obj, str) and fee_obj.isdigit():
        return int(fee_obj)
    # common nested keys used across different JSONs
    for k in ("fee_per_year_in_inr", "total_estimated_fee_in_inr", "fee", "estimated_fee_in_inr"):
        val = fee_obj.get(k) if isinstance(fee_obj, dict) else None
        if isinstance(val, (int, float)):
            return int(val)
        if isinstance(val, str) and val.isdigit():
            return int(val)
    # try to parse any numeric content
    if isinstance(fee_obj, dict):
        for v in fee_obj.values():
            try:
                return int(float(v))
            except Exception:
                continue
    return 0

# Optional language detection: try langdetect, otherwise fallback heuristic
def _fallback_detect(text):
    if not text:
        return "en"
    if re.search(r'[അ-ഹ]', text):  # Malayalam block
        return "ml"
    if re.search(r'[अ-ह]', text):  # Devanagari (Hindi) block
        return "hi"
    return "en"

try:
    from langdetect import detect as _ld_detect
    def detect(text):
        try:
            return _ld_detect(text)
        except Exception:
            return _fallback_detect(text)
except Exception:
    detect = _fallback_detect

def filter_colleges(colleges, location=None, course=None, budget=None, sort="rank"):
    nloc = _norm(location)
    ncourse = _norm(course)

    synonyms = {
        "cse": ["cse","computer","cs","computerscience","btech","btechcse"],
        "ai":  ["ai","ml","aiml","artificialintelligence","datascience","ds","aids"],
        "ece": ["ece","electronics","communication","electronicsandcommunication"],
        "mech":["mechanical","me","mech"],
        "civil":["civil","ce"],
        "bca": ["bca","computerapplications"],
        "bba": ["bba","business","management"],
    }

    def matches_course(course_list, needle):
        if not needle:
            return True
        blob = " ".join(_norm(x) for x in (course_list or []))
        expanded = {needle}
        for syn in synonyms.values():
            if needle in syn:
                expanded.update(syn)
        return any(w in blob for w in expanded)

    out = []
    for c in colleges:
        city_ok   = True if not nloc else (nloc in _norm(c.get("city","")) or nloc in _norm(c.get("state","")) or nloc in _norm(c.get("category","")))
        course_ok = matches_course(c.get("courses", []), ncourse)
        fee_ok    = True
        if budget:
            fees_struct = c.get("fees_structure") or {}
            min_fee = 10**12
            for v in (fees_struct.values() if isinstance(fees_struct, dict) else []):
                val = _extract_fee_value(v)
                if val and val < min_fee:
                    min_fee = val
            if min_fee == 10**12:
                min_fee = 0
            fee_ok = (min_fee <= int(budget))
        if city_ok and course_ok and fee_ok:
            out.append(c)

    # sorting
    if sort == "fee":
        def fee_key(x):
            fees_struct = x.get("fees_structure") or {}
            min_fee = 10**12
            for v in (fees_struct.values() if isinstance(fees_struct, dict) else []):
                val = _extract_fee_value(v)
                if val and val < min_fee:
                    min_fee = val
            return min_fee if min_fee < 10**12 else 10**12
        out.sort(key=fee_key)
    elif sort == "name":
        out.sort(key=lambda x: x.get("name","").lower())
    else:
        out.sort(key=lambda x: x.get("rank", 10**9))

    return out

SYSTEM_PROMPT = """You are EduGuide, a helpful AI assistant for college admissions in India.
When the user filters return no exact result, suggest 5–8 relevant colleges from the provided dataset with one-line reasons.
Be concise and practical.
"""

def gemini_suggest(location, course, budget):
    if not model:
        return "No close matches found. Try widening location, trying an alternate course name (e.g., CSE ↔ Computer Science), or increasing budget."
    try:
        dataset = json.dumps(COLLEGES, ensure_ascii=False)
        user_q  = f"location={location}, course={course}, budget={budget}"
        prompt  = f"{SYSTEM_PROMPT}\n\nDataset (JSON):\n{dataset}\n\nUser filters: {user_q}\n\nSuggestions:"
        resp    = model.generate_content(prompt)
        return (resp.text or "").strip()
    except Exception as e:
        print("❌ Gemini error:", e)
        return "No close matches found. Try widening location, trying an alternate course name, or increasing budget."

# ------------------ ROUTES ------------------ #
@app.route("/")
def home():
    top_colleges = sorted(COLLEGES, key=lambda x: x.get("rank", 10**9))[:20]
    return render_template("index.html", title="Home", colleges=top_colleges)

@app.route("/colleges")
def colleges_page():
    location = request.args.get("location", "").strip()
    course   = request.args.get("course", "").strip()
    budget   = request.args.get("budget", "").strip()
    sort     = request.args.get("sort", "rank")

    budget_int = int(budget) if budget.isdigit() else None

    results = filter_colleges(COLLEGES, location, course, budget_int, sort)

    if results:
        return render_template("colleges.html", title="Top Colleges", colleges=results)
    else:
        if model:
            try:
                dataset = json.dumps(COLLEGES, ensure_ascii=False)
                user_q  = f"location={location}, course={course}, budget={budget}"
                prompt  = f"{SYSTEM_PROMPT}\n\nDataset (JSON):\n{dataset}\n\nUser filters: {user_q}\n\nSuggestions:"
                resp = model.generate_content(prompt)
                gtext = resp.text or "⚠️ No close matches found. Try widening your search or changing filters."
            except Exception as e:
                print("Gemini error:", e)
                gtext = "⚠️ No close matches found. Try widening your search or changing filters."
        else:
            gtext = "⚠️ No AI model configured. Try widening your search or changing filters."
        return render_template("colleges.html", title="Top Colleges", colleges=[], gemini_text=gtext)

@app.route("/api/colleges")
def colleges_api():
    return jsonify(COLLEGES)

@app.route("/college/<int:college_id>")
def college_detail(college_id):
    # try to find by id, fallback to index/rank if id not present
    college = next((c for c in COLLEGES if c.get("id") == college_id), None)
    if not college:
        # fallback: try 0-based index == college_id
        if 0 <= college_id < len(COLLEGES):
            college = COLLEGES[college_id]
    if not college:
        return jsonify({"error":"Not found"}), 404
    return jsonify(college)

@app.route("/about")
def about():
    return render_template("about.html", title="About")

@app.route("/faq")
def faq():
    with open("data/faq.json", "r", encoding="utf-8") as f:
        faqs = json.load(f)
    return render_template("faq.html", title="FAQ", faqs=faqs)

@app.route("/contact")
def contact():
    return render_template("contact.html", title="Contact")

@app.route("/send_message", methods=["POST"])
def send_message():
    name = request.form.get("name"); email = request.form.get("email"); message = request.form.get("message")
    print(f"📩 Message from {name} ({email}): {message}")
    flash("✅ Your message has been sent successfully!", "success")
    return redirect(url_for("contact"))

# ------------- Chatbot ------------- #
def format_card_list(items):
    if not items:
        return "❌ No matching colleges found. Try refining filters."
    out = []
    for c in items[:8]:
        fee_text = ""
        fees_struct = c.get("fees_structure") or {}
        min_fee = None
        for v in (fees_struct.values() if isinstance(fees_struct, dict) else []):
            val = _extract_fee_value(v)
            if val:
                min_fee = val if (min_fee is None) else min(min_fee, val)
        if min_fee:
            fee_text = f" • Approx fee/yr: ₹{min_fee:,}"
        maps_part = " • 📍 Maps" if c.get("google_maps") else ""
        out.append(f"• {c.get('name','Unknown')} — {c.get('city','')}, {c.get('state','')} • Rank: {c.get('rank','N/A')}{fee_text}{maps_part}")
    return "\n".join(out)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_input = (data.get("message", "") or "").strip()
    # Try to pull filters from message
    loc_m = re.search(r"(in|at|location)\s*[:=]?\s*([a-zA-Z ]+)", user_input, re.I)
    crs_m = re.search(r"(course|stream|program)\s*[:=]?\s*([a-zA-Z &/]+)", user_input, re.I)
    fee_m = re.search(r"(budget|under|max|fee)\s*[:=]?\s*(\d{3,8})", user_input, re.I)

    location = (loc_m.group(2).strip() if loc_m else "")
    course   = (crs_m.group(2).strip() if crs_m else "")
    budget   = int(fee_m.group(2)) if fee_m else None

    # language preference: explicit param > detect
    lang_param = (data.get("language") or "").lower()
    if not lang_param:
        try:
            detected = detect(user_input) if user_input else "en"
        except Exception:
            detected = "en"
        if detected.startswith("ml"):
            lang_param = "ml"
        elif detected.startswith("hi"):
            lang_param = "hi"
        else:
            lang_param = "en"

    # keywords for recommendations
    keywords = ["recommend","suggest","college","cse","btech","ai","fee","budget","best","top"]
    if any(k in user_input.lower() for k in keywords) or location or course or budget:
        results = filter_colleges(COLLEGES, location, course, budget, "rank")
        if results:
            return jsonify({"response": format_card_list(results), "language": lang_param})
        else:
            return jsonify({"response": gemini_suggest(location, course, budget or ""), "language": lang_param})

    # If not a recommendation, fallback to Gemini structured reply (if available)
    if model:
        lang_instructions = {
            "en": "Respond in English.",
            "hi": "Respond in fluent, polite Hindi.",
            "ml": "Respond in fluent, polite Malayalam."
        }
        dataset_block = json.dumps(COLLEGES, ensure_ascii=False)
        prompt = f"""{SYSTEM_PROMPT}

Dataset:
{dataset_block}

Language instruction: {lang_instructions.get(lang_param, 'Respond in English.')}

User: {user_input}
Assistant:"""
        try:
            resp = model.generate_content(prompt)
            resp_text = (resp.text or "").strip() if resp else ""
            # Return text only; client will speak using browser TTS
            return jsonify({"response": resp_text, "language": lang_param})
        except Exception as e:
            print("❌ Gemini Error:", e)
            return jsonify({"response": "⚠️ Sorry, I couldn’t process your query.", "language": lang_param})
    else:
        help_text = (
            "Try queries like:\n"
            "• Show colleges in Kochi for CSE under 120000\n"
            "• Fees for AI & DS in Trivandrum\n"
            "• Top B.Tech colleges in Tamil Nadu\n"
        )
        return jsonify({"response": help_text, "language": lang_param})

# ------------------ ADMIN ------------------ #
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Simple admin login (development only)."""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        # dev credentials (change in production)
        if username == "admin" and password == "password":
            session["admin_logged_in"] = True
            flash("✅ Logged in as admin.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("❌ Invalid username or password.", "danger")
    return render_template("admin_login.html", title="Admin Login")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("🚪 Logged out.", "info")
    return redirect(url_for("home"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        flash("🔐 Please login to access the admin dashboard.", "warning")
        return redirect(url_for("admin_login"))
    return render_template("admin_dashboard.html", title="Admin Dashboard")

# ------------------ MAIN ------------------ #
if __name__ == "__main__":
    load_dotenv()
    print("Starting Flask app; model configured:", bool(model))
    app.run(debug=True)
