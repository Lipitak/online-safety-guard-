"""
app.py
------
ScamShield Backend API Orchestrator (Trinetra_ai SIH Project)

Exposing 4 Core Endpoints:
  1. /detect    (POST) -> Scam classification, category taxonomy, severity (critical vs moderate), & TTS parameters
  2. /explain   (POST) -> SHAP attribution & Post-Mortem separating User Mistakes vs System Gaps
  3. /check-url (POST) -> URL reputation checking via Google Safe Browsing / VirusTotal / Levenshtein fallback
  4. /translate (POST) -> Regional language detection & translation
"""

from flask import Flask, request, jsonify, render_template
from agents.translation_agent import TranslationAgent
from agents.detection_agent import DetectionAgent
from agents.explainability_agent import ExplainabilityAgent
from agents.url_reputation_agent import URLReputationAgent

app = Flask(__name__)

# Initialize 4 AI Agents
translation_agent = TranslationAgent()
detection_agent = DetectionAgent(pipeline_path="pipeline.pkl")
explainability_agent = ExplainabilityAgent(
    pipeline=detection_agent.pipeline,
    clean_text_fn=DetectionAgent.clean_text,
)
url_agent = URLReputationAgent()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/demo")
def phone_demo():
    return render_template("phone_demo.html")


@app.route("/detect", methods=["POST"])
def detect():
    """
    Main endpoint for Android ScamAccessibilityService & Chrome Extension.
    Input JSON: { "text": "...", "message": "...", "package_name": "com.whatsapp", "url": "..." }
    """
    data = request.get_json(force=True) or {}
    text = (data.get("text") or data.get("message") or data.get("content") or "").strip()
    package_name = data.get("package_name") or data.get("source_app") or ""
    url = data.get("url") or ""

    if not text and not url:
        return jsonify({"error": "No text or URL provided"}), 400

    # 1. Multi-Lingual Translation & Voice Payload
    translation = translation_agent.translate(text or url)
    english_text = translation["english_text"]

    # 2. Detection Agent & Category Taxonomy
    detection = detection_agent.analyze(english_text, package_name)
    verdict = detection["verdict"]
    confidence = detection["confidence"]
    category = detection["category"]
    severity = detection["severity"]

    # 3. URL Reputation Check if URL present
    url_check = url_agent.check(text or url)
    if url_check["is_dangerous"] or url_check["is_lookalike"]:
        verdict = "Scam"
        category = "phishing_link" if category == "generic" else category
        confidence = max(confidence, 0.90)
        severity = "critical"
    elif url_check["is_shortened"]:
        if verdict == "Safe":
            verdict = "Scam"
            confidence = max(confidence, 0.70)
            if severity == "none":
                severity = "moderate"

    is_scam = (verdict == "Scam")
    if is_scam and severity == "none":
        severity = "moderate"

    # Formulation of concise reason
    reason_parts = []
    if url_check.get("risk_note"):
        reason_parts.append(url_check["risk_note"])
    if translation.get("llm_reason"):
        reason_parts.append(translation["llm_reason"])
    if not reason_parts:
        reason_parts.append(f"Flagged by ScamShield AI Engine as {category.replace('_', ' ').title()} Scam")

    reason = "; ".join(dict.fromkeys(reason_parts))

    spoken_warning = {
        "text_local": translation["warning_local"],
        "text_english": translation["warning_english"],
        "speech_lang": translation["speech_lang"],
    }

    return jsonify({
        "is_scam": is_scam,
        "verdict": verdict,
        "category": category,
        "severity": severity,  # 'critical' or 'moderate' or 'none'
        "confidence": confidence,
        "reason": reason,
        "source_app": package_name or "unknown",
        "detected_language": translation["detected_language"],
        "spoken_warning": spoken_warning if severity == "critical" else None,
        "url_check": url_check
    })


@app.route("/explain", methods=["POST"])
def explain():
    data = request.get_json(force=True) or {}
    text = (data.get("text") or data.get("message") or "").strip()
    category = data.get("category", "generic")
    severity = data.get("severity", "critical")
    url = data.get("url", "")

    url_check = url_agent.check(text or url)
    cleaned = detection_agent.clean_text(text)

    explanation = explainability_agent.explain(
        raw_message=text,
        cleaned_message=cleaned,
        verdict="Scam",
        category=category,
        severity=severity,
        url_check=url_check
    )

    rem = explanation["remediation"]

    return jsonify({
        "threat_title": rem["threat_title"],
        "threat_summary": rem["threat_summary"],
        "user_mistakes": rem["user_mistakes"],
        "system_gaps": rem["system_gaps"],
        "remediation_steps": rem["remediation_steps"],
        "top_words": explanation["top_words"],
        "category": category,
        "severity": severity
    })


@app.route("/check-url", methods=["POST"])
def check_url():
    data = request.get_json(force=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    return jsonify(url_agent.check(url))


@app.route("/translate", methods=["POST"])
def translate_endpoint():
    data = request.get_json(force=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    return jsonify(translation_agent.translate(text))


# Legacy fallback endpoint
@app.route("/predict", methods=["POST"])
def predict():
    return detect()


@app.route("/analyze-page", methods=["POST"])
def analyze_page():
    data = request.get_json(force=True) or {}
    data["package_name"] = data.get("package_name", "com.android.chrome")
    res = detect().get_json()
    return jsonify(res)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)