import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session

from engine.question_engine import QuestionEngine
from engine.evaluator import Evaluator   # keep your existing evaluator

app = Flask(__name__)
app.secret_key = "aceinterview-secret-key"   # needed for session (duration timer)

engine   = QuestionEngine("questions.json")
evaluator = None  # Lazy init in submit

# Folder where video answers are saved
RESPONSES_DIR = os.path.join("responses", "videos")
os.makedirs(RESPONSES_DIR, exist_ok=True)


# ─────────────────────────────────────────
#  HOME
# ─────────────────────────────────────────
@app.route("/")
def home():
    return render_template("home.html")


# ─────────────────────────────────────────
#  START INTERVIEW
# ─────────────────────────────────────────
@app.route("/start")
def start():
    questions = engine.select_questions(12)

    # Store questions in session so /submit can access them
    session["questions"] = [
        {
            "id":       i + 1,
            "question": q["question"],
            "answer":   q.get("answer", ""),          # expected/model answer
            "topic":    q.get("topic", "General"),
            "keywords": q.get("keywords", [])
        }
        for i, q in enumerate(questions)
    ]
    session["start_time"] = datetime.now().isoformat()

    return render_template("interview.html", questions=session["questions"])


# ─────────────────────────────────────────
#  SUBMIT INTERVIEW
# ─────────────────────────────────────────
@app.route("/submit", methods=["POST"])
def submit():
    questions  = session.get("questions", [])
    start_time = session.get("start_time")

    # ── Calculate session duration ──────────────────────
    duration_str = "—"
    if start_time:
        try:
            delta = datetime.now() - datetime.fromisoformat(start_time)
            mins  = int(delta.total_seconds() // 60)
            secs  = int(delta.total_seconds() % 60)
            duration_str = f"{mins:02d}:{secs:02d}"
        except Exception:
            pass

    # ── Process each question ───────────────────────────
    report_questions = []

    for q in questions:
        qid        = q["id"]
        is_skipped = request.form.get(f"skipped_{qid}") == "1"
        video_file = request.files.get(f"video_{qid}")
        confidence = int(request.form.get(f"confidence_{qid}", 0))

        if is_skipped or not video_file or video_file.filename == "":
            # ── Skipped / no recording ──────────────────
            report_questions.append({
                "id":         qid,
                "text":       q["question"],
                "topic":      q["topic"],
                "score":      0,
                "confidence": 0,
                "status":     "skipped"
            })
            continue

        # ── Save video to disk ──────────────────────────
        video_filename = f"answer_{qid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"
        video_path     = os.path.join(RESPONSES_DIR, video_filename)
        video_file.save(video_path)

        # ── Score calculation ───────────────────────────
        global evaluator
        if evaluator is None:
            try:
                evaluator = Evaluator()
            except Exception as e:
                print(f"Evaluator init failed: {e}")
                evaluator = None
        
        # Right now we use confidence as the primary signal since answers
        # are video (no text to run NLP on).
        # When you add speech-to-text later, swap this block with:
        #   transcript = transcribe(video_path)
        #   nlp_score  = evaluator.evaluate(transcript, q["answer"], q["keywords"])
        #   score = round(0.6 * nlp_score + 0.4 * confidence)

        score = confidence   # placeholder until STT is added

        report_questions.append({
            "id":         qid,
            "text":       q["question"],
            "topic":      q["topic"],
            "score":      score,
            "confidence": confidence,
            "status":     "answered",
            "video":      video_filename
        })

    # ── Build topic aggregates ──────────────────────────
    topic_map = {}
    for rq in report_questions:
        t = rq["topic"]
        if t not in topic_map:
            topic_map[t] = {"scores": [], "total": 0, "answered": 0}
        topic_map[t]["total"] += 1
        if rq["status"] == "answered":
            topic_map[t]["scores"].append(rq["score"])
            topic_map[t]["answered"] += 1

    topics = []
    for name, data in topic_map.items():
        avg = round(sum(data["scores"]) / len(data["scores"])) if data["scores"] else 0
        topics.append({
            "name":      name,
            "score":     avg,
            "questions": data["total"],
            "answered":  data["answered"]
        })

    # ── Overall score (avg of answered only) ───────────
    answered_qs = [rq for rq in report_questions if rq["status"] == "answered"]
    overall     = round(sum(rq["score"] for rq in answered_qs) / len(answered_qs)) if answered_qs else 0

    # ── Auto-generate strengths & improvements ──────────
    sorted_topics = sorted(topics, key=lambda t: t["score"], reverse=True)

    strengths = []
    for t in sorted_topics:
        if t["answered"] > 0 and t["score"] >= 70:
            strengths.append(f"Strong {t['name']} knowledge ({t['score']}%)")
    if not strengths:
        strengths = ["Completed the interview session", "Showed willingness to attempt questions"]

    improve = []
    for t in sorted_topics:
        if t["answered"] > 0 and t["score"] < 70:
            improve.append(f"Revise {t['name']} concepts — scored {t['score']}%")
    skipped_topics = [rq["topic"] for rq in report_questions if rq["status"] == "skipped"]
    for st in set(skipped_topics):
        improve.append(f"Attempt skipped {st} questions next time")
    if not improve:
        improve = ["Keep practicing for even better results"]

    # ── Build final report dict ─────────────────────────
    report = {
        "overall":   overall,
        "answered":  len(answered_qs),
        "skipped":   len([rq for rq in report_questions if rq["status"] == "skipped"]),
        "total":     len(report_questions),
        "duration":  duration_str,
        "topics":    topics,
        "questions": report_questions,
        "strengths": strengths[:3],    # top 3
        "improve":   improve[:4],      # top 4
    }

    # ── Save report JSON for records ────────────────────
    report_path = os.path.join("responses", f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    # ── Store in session and render result ──────────────
    session["report"] = report
    return render_template("result.html", report=report)


# ─────────────────────────────────────────
#  RESULT  (direct URL visit fallback)
# ─────────────────────────────────────────
@app.route("/result")
def result():
    report = session.get("report")
    if not report:
        # No session data — redirect to home
        return redirect(url_for("home"))
    return render_template("result.html", report=report)


# ─────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)