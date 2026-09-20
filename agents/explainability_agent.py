"""
explainability_agent.py
------------------------
Agent 2: ExplainabilityAgent (ScamShield SIH Project)
Provides SHAP attribution & Security Post-Mortem Remediation Plans.
Separates User Security Mistakes from System/Security Gaps.
"""

import re
import shap

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+|bit\.ly\S*", re.IGNORECASE)
URGENCY_WORDS = {
    "urgent", "immediately", "verify", "suspend", "blocked", "act now",
    "click here", "limited time", "winner", "congratulations", "otp",
    "account will be", "final notice", "expire", "action required",
    "deactivated", "lottery", "prize", "penalty", "legal action"
}


class ExplainabilityAgent:
    def __init__(self, pipeline, clean_text_fn):
        self.pipeline = pipeline
        self.clean_text = clean_text_fn

        def predict_proba_wrapper(texts):
            cleaned = [self.clean_text(t) for t in texts]
            return self.pipeline.predict_proba(cleaned)

        try:
            masker = shap.maskers.Text(tokenizer=r"\W+")
            self.explainer = shap.Explainer(
                predict_proba_wrapper, masker, output_names=["Safe", "Scam"]
            )
        except Exception as e:
            print("SHAP Initialization Warning:", e)
            self.explainer = None

    def _top_shap_words(self, cleaned_message: str, top_n=4) -> list:
        if not self.explainer or not cleaned_message:
            return []
        try:
            shap_values = self.explainer([cleaned_message])
            words = shap_values.data[0]
            scam_scores = shap_values.values[0][:, 1]
            ranked = sorted(zip(words, scam_scores), key=lambda x: x[1], reverse=True)
            return [w.strip() for w, score in ranked if score > 0 and len(w.strip()) > 2][:top_n]
        except Exception:
            return []

    def generate_remediation_plan(
        self,
        raw_content: str,
        category: str,
        severity: str,
        url_check: dict = None,
        llm_reason: str = None
    ) -> dict:
        """
        Generates structured Post-Mortem Analysis for ScamShield.
        Separates User Security Mistakes vs System Security Gaps.
        """
        lowered = raw_content.lower()

        # 1. Threat Title
        titles = {
            "banking_otp": "Alert: Banking Credential & OTP Theft Attack",
            "job_offer": "Alert: Fraudulent Job Offer & WFH Payment Scam",
            "lottery_prize": "Alert: Advance-Fee Fake Lottery & Reward Scam",
            "phishing_link": "Alert: Malicious Phishing Domain Impersonation",
            "romance_investment": "Alert: Crypto / Financial Investment Trap",
            "generic": "Alert: Cyber Coercion & Fraudulent Content"
        }
        threat_title = titles.get(category, "Alert: Cyber Scam Threat")

        # 2. Identify User Mistakes vs System Gaps
        user_mistakes = []
        system_gaps = []

        if "otp" in lowered or "pin" in lowered:
            user_mistakes.append("User shared or entered confidential OTP / Banking PIN on an unverified platform.")
        if URL_PATTERN.search(lowered):
            user_mistakes.append("User clicked an unverified SMS / chat link instead of typing official domain names.")
        if any(w in lowered for w in URGENCY_WORDS):
            user_mistakes.append("User acted under artificial urgency and panic threats without verifying authenticity.")

        if url_check and url_check.get("has_url"):
            if url_check.get("is_lookalike"):
                system_gaps.append("Domain Spoofing: Bad actor deployed a typosquatted domain mimicking an official brand.")
            if url_check.get("is_shortened"):
                system_gaps.append("URL Masking: True destination URL was hidden behind a URL shortener service.")
            if url_check.get("suspicious_tld"):
                system_gaps.append("Untrusted TLD: Fraudulent website operated on an unverified high-risk TLD.")
            if url_check.get("is_ip"):
                system_gaps.append("Missing Transport Security: Hostname used raw IP address lacking verified SSL certificates.")

        if not user_mistakes:
            user_mistakes.append("Interaction with unverified third-party message sender or link.")
        if not system_gaps:
            system_gaps.append("Social engineering exploitation bypassing traditional network spam filters.")

        # 3. Actionable Remediation Steps
        remediation_steps = [
            "🚨 DO NOT SHARE OTP/PIN: Never share banking OTPs, CVVs, or UPI PINs with anyone.",
            "🛡️ SAFE EXIT: Close this message or browser window immediately.",
            "🔒 CREDENTIAL RESET: If credentials were entered, reset banking passwords immediately from official apps.",
            "📲 ENABLE 2FA: Turn on Multi-Factor Authentication (2FA) via authenticator apps.",
            "📢 REPORT THREAT: Report this fraudulent message to CERT-In / National Cyber Crime Portal (cybercrime.gov.in)."
        ]

        return {
            "threat_title": threat_title,
            "threat_summary": llm_reason or "Social engineering attack attempting to capture sensitive data or money.",
            "user_mistakes": user_mistakes,
            "system_gaps": system_gaps,
            "remediation_steps": remediation_steps,
            "severity": severity,
            "category": category
        }

    def explain(
        self,
        raw_message: str,
        cleaned_message: str,
        verdict: str,
        category: str = "generic",
        severity: str = "moderate",
        url_check: dict = None,
        llm_reason: str = None
    ) -> dict:
        top_words = self._top_shap_words(cleaned_message) if verdict == "Scam" else []
        remediation = self.generate_remediation_plan(
            raw_content=raw_message,
            category=category,
            severity=severity,
            url_check=url_check,
            llm_reason=llm_reason
        )

        reason_parts = []
        if top_words:
            reason_parts.append(f"Trigger phrases: {', '.join(top_words)}")
        if url_check and url_check.get("risk_note"):
            reason_parts.append(url_check["risk_note"])
        if not reason_parts:
            reason_parts.append("Scam patterns detected by ScamShield AI Engine")

        return {
            "reason": "; ".join(reason_parts),
            "top_words": top_words,
            "remediation": remediation,
        }
