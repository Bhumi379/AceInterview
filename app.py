from flask import Flask, render_template, request, redirect, url_for
from engine.question_engine import QuestionEngine

app = Flask(__name__)

engine = QuestionEngine("questions.json")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/start")
def start():
    questions = engine.select_questions(12)
    return render_template("interview.html", questions=questions)

@app.route("/submit", methods=["POST"])
def submit():
    
    answers = request.form
    
    # store answers
    for i, ans in answers.items():
        engine.responses.append({
            "question_id": i,
            "text_answer": ans
        })

    engine.save_responses()

    return redirect(url_for("result"))

@app.route("/result")
def result():
    return render_template("result.html")

if __name__ == "__main__":
    app.run(debug=True)