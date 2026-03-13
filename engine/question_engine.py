import json
import random

class QuestionEngine:

    def __init__(self, question_file):
        self.question_file = question_file
        self.questions = self.load_questions()
        self.selected_questions = []
        self.responses = []

    def load_questions(self):
        with open(self.question_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    def select_questions(self, num_questions=12):
        self.selected_questions = random.sample(self.questions, num_questions)
        return self.selected_questions

    def store_response(self, question, text_answer, video_path):
        response = {
            "question": question["question"],
            "topic": question["topic"],
            "difficulty": question["difficulty"],
            "text_answer": text_answer,
            "video_answer": video_path
        }

        self.responses.append(response)

    def save_responses(self, output_file="responses/responses.json"):
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.responses, f, indent=4)