"""
app.py
------
Step 7: Backend API

Loads the trained pipeline (pipeline.pkl) and serves:
  - GET  /                -> simple web UI (index.html)
  - POST /predict         -> {"message": "..."} -> {verdict, confidence, reason, top_words}

SHAP is used to explain WHY a message was flagged, by finding which words
pushed the prediction toward "Scam".
"""

import re
import string
import joblib
import numpy as np
import shap
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# -----------------------------
# Load trained pipeline
# -----------------------------
pipeline = joblib.load("pipeline.pkl")

# Simple heuristic flags we can detect directly on raw text (fast, on top of the ML model).
# These make the "reason" more human-readable alongside the SHAP words.
URL_PATTERN = re.compile(r"http\S+|www\S+|bit\.ly\S*")
URGENCY_WORDS = {
    "urgent", "immediately", "verify", "suspend", "blocked", "act now",
    "click here", "limited time", "winner", "congratulations", "otp",
    "account will be", "final notice", "expire",
}


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+", " link ", text)
    text = re.sub(r"\d{6,}", " longnum ", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def predict_proba_wrapper(texts):
    """Wrapper so SHAP can call the pipeline on raw text lists."""
    cleaned = [clean_text(t) for t in texts]
    return pipeline.predict_proba(cleaned)


# SHAP text explainer: masks out words one at a time to see which ones
# push the prediction toward "Scam" (class index 1).
masker = shap.maskers.Text(tokenizer=r"\W+")
explainer = shap.Explainer(predict_proba_wrapper, masker, output_names=["Safe", "Scam"])


def get_top_reason_words(message, top_n=3):
    """Return the top words that pushed this message toward 'Scam'."""
    shap_values = explainer([message])
    words = shap_values.data[0]
    scam_scores = shap_values.values[0][:, 1]  # contribution to "Scam" class

    ranked = sorted(zip(words, scam_scores), key=lambda x: x[1], reverse=True)
    top = [w.strip() for w, score in ranked if score > 0 and w.strip()][:top_n]
    return top


def detect_flags(raw_message):
    flags = []
    if URL_PATTERN.search(raw_message.lower()):
        flags.append("contains a link")
    lowered = raw_message.lower()
    if any(word in lowered for word in URGENCY_WORDS):
        flags.append("uses urgent/pressure language")
    return flags


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/demo")
def phone_demo():
    return render_template("phone_demo.html")


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True)
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"error": "No message provided"}), 400

    cleaned = clean_text(message)
    proba = pipeline.predict_proba([cleaned])[0]  # [P(Safe), P(Scam)]
    scam_prob = float(proba[1])
    verdict = "Scam" if scam_prob >= 0.5 else "Safe"
    confidence = round(scam_prob if verdict == "Scam" else 1 - scam_prob, 3)

    reason_parts = []

    # Rule-based quick flags (fast, human-readable)
    quick_flags = detect_flags(message)
    reason_parts.extend(quick_flags)

    # SHAP-based top contributing words (only computed when flagged as Scam,
    # to keep the demo fast — SHAP on every request is heavier)
    top_words = []
    if verdict == "Scam":
        try:
            top_words = get_top_reason_words(cleaned, top_n=3)
            if top_words:
                reason_parts.append(f"suspicious phrases: {', '.join(top_words)}")
        except Exception:
            pass  # fail gracefully in a live demo, quick_flags still shows

    if not reason_parts:
        reason_parts.append("no strong scam indicators found" if verdict == "Safe"
                             else "unusual word patterns detected")

    return jsonify({
        "verdict": verdict,
        "confidence": confidence,
        "reason": "; ".join(reason_parts),
        "top_words": top_words,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5002)
