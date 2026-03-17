import os
import json
from datetime import datetime, timedelta

from flask import (Flask, render_template, request,
                   redirect, url_for, session, flash)
from flask_login import (LoginManager, UserMixin,
                         login_user, logout_user,
                         login_required, current_user)
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

# Assuming your engine files exist in the project directory
# from engine.question_engine import QuestionEngine
# from engine.evaluator import Evaluator

app = Flask(__name__)
# ─────────────────────────────────────────
#  SECURITY & SESSION CONFIG
# ─────────────────────────────────────────
app.secret_key = "aceinterview-super-secret-2026" # Changed to current year
app.config["SQLALCHEMY_DATABASE_URI"]        = "sqlite:///aceinterview.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PERMANENT_SESSION_LIFETIME"]     = timedelta(minutes=60) # Sessions expire after 1 hour

db            = SQLAlchemy(app)
bcrypt        = Bcrypt(app)
login_manager = LoginManager(app)

# Redirect unauthorized users to login
login_manager.login_view             = "login"
login_manager.login_message          = "You need to log in to start an interview."
login_manager.login_message_category = "info"

# engine = QuestionEngine("questions.json")
# evaluator = Evaluator()

# ... (MODELS REMAIN THE SAME AS YOUR PREVIOUS CODE) ...

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    email       = db.Column(db.String(200), unique=True, nullable=False)
    password    = db.Column(db.String(200), nullable=False)
    college     = db.Column(db.String(200), default="")
    target_role = db.Column(db.String(100), default="Software Engineer")
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)
    reports     = db.relationship("Report", backref="user", lazy=True)

class Report(db.Model):
    __tablename__ = "reports"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    overall     = db.Column(db.Integer, default=0)
    report_json = db.Column(db.Text,      default="{}")
    created_at  = db.Column(db.DateTime,  default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─────────────────────────────────────────
#  UPDATED ROUTES
# ─────────────────────────────────────────

@app.route("/")
def home():
    # Pass user name if logged in to display in footer
    user_name = current_user.name if current_user.is_authenticated else None
    return render_template("home.html", user_name=user_name)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user     = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session.permanent = True
            login_user(user, remember=True)
            return redirect(url_for("dashboard"))

        # If login fails, we pass the 'request.form' so the user doesn't have to re-type their email
        return render_template("login.html", error="Invalid credentials.", form=request.form)

    # Initial GET request: pass an empty dictionary so 'form' is defined but empty
    return render_template("login.html", error=None, form={})

@app.route("/dashboard")
@login_required
def dashboard():
    # Fetch user reports for the dashboard
    reports = current_user.reports
    return render_template("dashboard.html", user=current_user, reports=reports)

@app.route("/start")
@login_required # SYSTEM CHECKS IF USER IS REGISTERED HERE
def start():
    # Your existing interview logic
    return render_template("interview.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)