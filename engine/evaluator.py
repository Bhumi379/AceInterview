from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class Evaluator:

    def __init__(self):
        # load semantic model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    # -------- Keyword Score --------
    def keyword_score(self, user_answer, keywords):

        user_answer = user_answer.lower()

        matched = 0

        for word in keywords:
            if word.lower() in user_answer:
                matched += 1

        score = matched / len(keywords)

        return score

    # -------- Semantic Similarity --------
    def semantic_score(self, user_answer, ideal_answer):

        embeddings = self.model.encode([user_answer, ideal_answer])

        similarity = cosine_similarity(
            [embeddings[0]],
            [embeddings[1]]
        )[0][0]

        return similarity

    # -------- Final Evaluation --------
    def evaluate(self, user_answer, ideal_answer, keywords):

        k_score = self.keyword_score(user_answer, keywords)

        s_score = self.semantic_score(user_answer, ideal_answer)

        final_score = (0.4 * k_score) + (0.6 * s_score)

        return {
            "keyword_score": round(k_score, 2),
            "semantic_score": round(s_score, 2),
            "final_score": round(final_score * 100, 2)
        }
