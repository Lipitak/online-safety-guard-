"""
detection_agent.py
-------------------
Agent 1: DetectionAgent

Responsibility: take a raw message and decide Scam vs Safe using the
trained TF-IDF + Naive Bayes pipeline, returning a verdict + confidence.

This agent does ONE job only: classification. It does not explain WHY —
that's the ExplainabilityAgent's job (separation of concerns).
"""

import re
import string
import joblib


class DetectionAgent:
    def __init__(self, pipeline_path="pipeline.pkl"):
        self.pipeline = joblib.load(pipeline_path)

    @staticmethod
    def clean_text(text):
        text = str(text).lower()
        text = re.sub(r"http\S+|www\S+", " link ", text)
        text = re.sub(r"\d{6,}", " longnum ", text)
        text = text.translate(str.maketrans("", "", string.punctuation))
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def analyze(self, message: str) -> dict:
        """
        Returns:
            {
                "verdict": "Scam" | "Safe",
                "confidence": float (0-1),
                "cleaned_text": str   # passed along for other agents to reuse
            }
        """
        cleaned = self.clean_text(message)
        proba = self.pipeline.predict_proba([cleaned])[0]  # [P(Safe), P(Scam)]
        scam_prob = float(proba[1])
        verdict = "Scam" if scam_prob >= 0.5 else "Safe"
        confidence = round(scam_prob if verdict == "Scam" else 1 - scam_prob, 3)

        return {
            "verdict": verdict,
            "confidence": confidence,
            "cleaned_text": cleaned,
        }