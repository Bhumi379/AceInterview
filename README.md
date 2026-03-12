# AceInterview AI 🚀

An AI-powered mock interview preparation platform that evaluates technical answers and communication skills to help candidates prepare for real-world technical interviews.

---

## 📌 Overview

AceInterview AI is an intelligent interview practice platform designed to simulate real technical interviews. The system asks structured interview questions, evaluates candidate responses using Natural Language Processing, and provides detailed feedback to help users improve their technical knowledge and communication skills.

The platform analyzes answers using keyword matching and semantic similarity techniques to determine how well a candidate understands the concept.

---

## 🎯 Features

* Interactive mock interview sessions
* Topic-based interview questions (DSA, OOP, DBMS, OS, etc.)
* AI-powered answer evaluation
* Keyword and semantic similarity scoring
* Topic-wise performance analysis
* Interview feedback and improvement suggestions
* Structured JSON-based question database

---

## 🧠 How It Works

1. User starts an interview session.
2. The system selects 12–15 questions from the question database.
3. Questions are presented one by one.
4. The user submits answers through the interface.
5. The system evaluates answers using NLP techniques.
6. A final interview report is generated with scores and feedback.

---

## 🏗️ System Architecture

Frontend
HTML
Tailwind CSS
JavaScript

Backend
Python
Flask

NLP & Evaluation
spaCy

Data Storage
JSON Question Dataset

---

## 📂 Project Structure

ai-interview-system

app.py
questions.json
evaluator.py

templates

* home.html
* setup.html
* interview.html
* result.html

static

* css
* js

utils

* question_selector.py

---

## 📊 Evaluation Method

Each answer is evaluated using a hybrid scoring system:

Final Score =
60% Semantic Similarity
40% Keyword Coverage

The system also analyzes response length and clarity to provide communication feedback.

---

## 📈 Example Output

Interview Score: 74%

Topic Performance
DSA → 78%
OOP → 70%
DBMS → 65%
OS → 80%

Areas to Improve

* Database normalization
* Time complexity analysis

---

## 🚀 Future Improvements

* Voice-based interview responses
* Real-time follow-up questions
* Large language model based evaluation
* Resume-based personalized interviews
* Cloud deployment

---

## 💡 Motivation

Preparing for technical interviews can be difficult without structured feedback. AceInterview AI aims to simulate real interview scenarios and provide intelligent insights to help candidates improve their performance.

---

## 👩‍💻 Author

Bhumi Sharma
B.Tech IT – Banasthali Vidyapith

Interests: Web Development, Machine Learning, and Intelligent Systems

---
