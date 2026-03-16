import os
import json
from datetime import datetime

from flask import (Flask, render_template, request,
                   redirect, url_for, session, flash)
from flask_login import (LoginManager, UserMixin,
                         login_user, logout_user,
                         login_required, current_user)
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

from engine.question_engine import QuestionEngine
from engine.evaluator import Evaluator

# ─────────────────────────────────────────
#  APP CONFIG
# ─────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "aceinterview-super-secret-2024"

app.config["SQLALCHEMY_DATABASE_URI"]        = "sqlite:///aceinterview.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db            = SQLAlchemy(app)
bcrypt        = Bcrypt(app)
login_manager = LoginManager(app)

login_manager.login_view             = "login"
login_manager.login_message          = "Please log in to continue."
login_manager.login_message_category = "info"

engine    = QuestionEngine("questions.json")
evaluator = Evaluator()

RESPONSES_DIR = os.path.join("responses", "videos")
os.makedirs(RESPONSES_DIR, exist_ok=True)
os.makedirs("responses",   exist_ok=True)


# ─────────────────────────────────────────
#  MODELS
# ─────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    email       = db.Column(db.String(200), unique=True, nullable=False)
    password    = db.Column(db.String(200), nullable=False)
    college     = db.Column(db.String(200), default="")
    target_role = db.Column(db.String(100), default="Software Engineer")
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)
    reports     = db.relationship("Report", backref="user", lazy=True,
                                  order_by="Report.created_at.desc()")


class Report(db.Model):
    __tablename__ = "reports"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    overall     = db.Column(db.Integer, default=0)
    answered    = db.Column(db.Integer, default=0)
    skipped     = db.Column(db.Integer, default=0)
    total       = db.Column(db.Integer, default=0)
    duration    = db.Column(db.String(20), default="—")
    report_json = db.Column(db.Text,      default="{}")
    created_at  = db.Column(db.DateTime,  default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─────────────────────────────────────────
#  HOME
# ─────────────────────────────────────────
@app.route("/")
def home():
    return render_template("home.html")


# ─────────────────────────────────────────
#  SIGNUP
# ─────────────────────────────────────────
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        email       = request.form.get("email", "").strip().lower()
        password    = request.form.get("password", "")
        confirm     = request.form.get("confirm", "")
        college     = request.form.get("college", "").strip()
        target_role = request.form.get("target_role", "Software Engineer")

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email or "@" not in email:
            errors.append("Valid email is required.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")

        if errors:
            return render_template("signup.html", errors=errors, form=request.form)

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        user   = User(name=name, email=email, password=hashed,
                      college=college, target_role=target_role)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("dashboard"))

    return render_template("signup.html", errors=[], form={})


# ─────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"
        user     = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))

        return render_template("login.html",
                               error="Invalid email or password.",
                               form=request.form)

    return render_template("login.html", error=None, form={})


# ─────────────────────────────────────────
#  LOGOUT
# ─────────────────────────────────────────
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# ─────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    reports = current_user.reports

    trend = [
        {
            "date":     r.created_at.strftime("%d %b"),
            "score":    r.overall,
            "answered": r.answered,
            "total":    r.total,
        }
        for r in reversed(reports[:8])
    ]

    topic_totals = {}
    for r in reports:
        try:
            data = json.loads(r.report_json)
            for t in data.get("topics", []):
                if t["answered"] > 0:
                    nm = t["name"]
                    if nm not in topic_totals:
                        topic_totals[nm] = []
                    topic_totals[nm].append(t["score"])
        except Exception:
            pass

    topic_averages = sorted(
        [{"name": k, "score": round(sum(v) / len(v))} for k, v in topic_totals.items()],
        key=lambda x: x["score"], reverse=True
    )

    stats = {
        "sessions":   len(reports),
        "best_score": max((r.overall for r in reports), default=0),
        "avg_score":  round(sum(r.overall for r in reports) / len(reports)) if reports else 0,
        "total_qs":   sum(r.answered for r in reports),
    }

    return render_template("dashboard.html",
                           user=current_user,
                           reports=reports[:10],
                           trend=trend,
                           topic_averages=topic_averages,
                           stats=stats)


# ─────────────────────────────────────────
#  START INTERVIEW
# ─────────────────────────────────────────
@app.route("/start")
@login_required
def start():
    questions = engine.select_questions(12)
    session["questions"] = [
        {
            "id":       i + 1,
            "question": q["question"],
            "answer":   q.get("answer", ""),
            "topic":    q.get("topic", "General"),
            "keywords": q.get("keywords", [])
        }
        for i, q in enumerate(questions)
    ]
    session["start_time"] = datetime.now().isoformat()
    return render_template("interview.html", questions=session["questions"])


# ─────────────────────────────────────────
#  SUBMIT
# ─────────────────────────────────────────
@app.route("/submit", methods=["POST"])
@login_required
def submit():
    questions    = session.get("questions", [])
    start_time   = session.get("start_time")
    duration_str = "—"

    if start_time:
        try:
            delta        = datetime.now() - datetime.fromisoformat(start_time)
            mins         = int(delta.total_seconds() // 60)
            secs         = int(delta.total_seconds() %  60)
            duration_str = f"{mins:02d}:{secs:02d}"
        except Exception:
            pass

    report_questions = []
    for q in questions:
        qid        = q["id"]
        is_skipped = request.form.get(f"skipped_{qid}") == "1"
        video_file = request.files.get(f"video_{qid}")
        confidence = int(request.form.get(f"confidence_{qid}", 0))

        if is_skipped or not video_file or video_file.filename == "":
            report_questions.append({
                "id": qid, "text": q["question"], "topic": q["topic"],
                "score": 0, "confidence": 0, "status": "skipped"
            })
            continue

        fname = f"user{current_user.id}_q{qid}_{datetime.now().strftime('%Y%m%d%H%M%S')}.webm"
        video_file.save(os.path.join(RESPONSES_DIR, fname))

        # Score = confidence until speech-to-text is added.
        # Future: transcript = transcribe(path)
        #         score = evaluator.evaluate(transcript, q["answer"], q["keywords"])
        score = confidence

        report_questions.append({
            "id": qid, "text": q["question"], "topic": q["topic"],
            "score": score, "confidence": confidence,
            "status": "answered", "video": fname
        })

    topic_map = {}
    for rq in report_questions:
        t = rq["topic"]
        if t not in topic_map:
            topic_map[t] = {"scores": [], "total": 0, "answered": 0}
        topic_map[t]["total"] += 1
        if rq["status"] == "answered":
            topic_map[t]["scores"].append(rq["score"])
            topic_map[t]["answered"] += 1

    topics = [
        {
            "name":      name,
            "score":     round(sum(d["scores"]) / len(d["scores"])) if d["scores"] else 0,
            "questions": d["total"],
            "answered":  d["answered"]
        }
        for name, d in topic_map.items()
    ]

    answered_qs = [rq for rq in report_questions if rq["status"] == "answered"]
    overall     = round(sum(rq["score"] for rq in answered_qs) / len(answered_qs)) if answered_qs else 0

    sorted_t  = sorted(topics, key=lambda t: t["score"], reverse=True)
    strengths = [f"Strong {t['name']} knowledge ({t['score']}%)" for t in sorted_t if t["answered"] > 0 and t["score"] >= 70][:3]
    improve   = [f"Revise {t['name']} concepts — scored {t['score']}%" for t in sorted_t if t["answered"] > 0 and t["score"] < 70][:3]
    improve  += [f"Attempt skipped {tp} questions next time"
                 for tp in list({rq["topic"] for rq in report_questions if rq["status"] == "skipped"})[:2]]

    if not strengths: strengths = ["Completed the full interview session"]
    if not improve:   improve   = ["Keep practicing for even better results"]

    report = {
        "overall":   overall,
        "answered":  len(answered_qs),
        "skipped":   len(report_questions) - len(answered_qs),
        "total":     len(report_questions),
        "duration":  duration_str,
        "topics":    topics,
        "questions": report_questions,
        "strengths": strengths,
        "improve":   improve,
        "user_name": current_user.name,
    }

    db_report = Report(
        user_id=current_user.id, overall=overall,
        answered=report["answered"], skipped=report["skipped"],
        total=report["total"], duration=duration_str,
        report_json=json.dumps(report),
    )
    db.session.add(db_report)
    db.session.commit()

    session["report"] = report
    return render_template("result.html", report=report)


# ─────────────────────────────────────────
#  RESULT (direct URL fallback)
# ─────────────────────────────────────────
@app.route("/result")
@login_required
def result():
    report = session.get("report")
    if not report:
        return redirect(url_for("dashboard"))
    return render_template("result.html", report=report)


# ─────────────────────────────────────────
#  VIEW PAST REPORT
# ─────────────────────────────────────────
@app.route("/report/<int:report_id>")
@login_required
def view_report(report_id):
    r = Report.query.get_or_404(report_id)
    if r.user_id != current_user.id:
        return redirect(url_for("dashboard"))
    return render_template("result.html", report=json.loads(r.report_json))


# ─────────────────────────────────────────
#  INIT DB + RUN
# ─────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)