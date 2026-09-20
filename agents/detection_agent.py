"""
detection_agent.py
-------------------
Agent 1: DetectionAgent (ScamShield SIH Project)
Context-Aware Multi-Feature Scam Taxonomy Classifier & Severity Engine
"""

import re
import string
import joblib

CATEGORY_PATTERNS = {
    "banking_otp": [
        r"\botp\b", r"\bpin\b", r"cvv", r"sbi", r"hdfc", r"icici", r"axis", r"kotak", r"netbanking",
        r"bank\s+account", r"debit\s+card", r"credit\s+card", r"card\s+blocked", r"kyc\s+expir",
        r"kyc\s+update", r"pan\s+card", r"upi\s+pin", r"transfer\s+money", r"verify\s+account"
    ],
    "job_offer": [
        r"job\s+offer", r"naukri", r"part\s*time\s*job", r"work\s+from\s+home", r"daily\s+income",
        r"earn\s+rs", r"telegram\s+group", r"task\s+based", r"hiring\s+immediately", r"salary\s+rs", r"\bjob\b"
    ],
    "lottery_prize": [
        r"lottery", r"won\s+rs", r"winner", r"congratulations", r"claim\s+your\s+reward",
        r"cashback", r"lucky\s+draw", r"free\s+gift"
    ],
    "romance_investment": [
        r"crypto\s+investment", r"forex\s+trading", r"guaranteed\s+returns", r"double\s+your\s+money",
        r"bitcoin\s+profit", r"whatsapp\s+investment"
    ],
    "phishing_link": [
        r"click\s+here", r"\.xyz", r"\.top", r"\.online"
    ]
}

CRITICAL_CATEGORIES = {"banking_otp", "kyc_expiry", "card_block", "upi_fraud"}


class DetectionAgent:
    def __init__(self, pipeline_path="pipeline.pkl"):
        try:
            self.pipeline = joblib.load(pipeline_path)
        except Exception as e:
            print("DetectionAgent: Warning loading pipeline:", e)
            self.pipeline = None

    @staticmethod
    def clean_text(text: str) -> str:
        text = str(text).lower()
        text = re.sub(r"http\S+|www\S+", " link ", text)
        text = re.sub(r"\d{6,}", " longnum ", text)
        text = text.translate(str.maketrans("", "", string.punctuation))
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def classify_category(self, text: str, package_name: str = "") -> str:
        lowered = text.lower()
        pkg = (package_name or "").lower()

        # 1. Banking / OTP / KYC (Highest Priority -> Critical)
        if any(re.search(pat, lowered) for pat in CATEGORY_PATTERNS["banking_otp"]):
            return "banking_otp"

        # 2. Job Offer (Naukri/LinkedIn or Job patterns -> Moderate)
        if "naukri" in pkg or "linkedin" in pkg or any(re.search(pat, lowered) for pat in CATEGORY_PATTERNS["job_offer"]):
            return "job_offer"

        # 3. Lottery / Prize -> Moderate
        if any(re.search(pat, lowered) for pat in CATEGORY_PATTERNS["lottery_prize"]):
            return "lottery_prize"

        # 4. Romance / Investment -> Moderate
        if any(re.search(pat, lowered) for pat in CATEGORY_PATTERNS["romance_investment"]):
            return "romance_investment"

        # 5. Phishing Link
        if any(re.search(pat, lowered) for pat in CATEGORY_PATTERNS["phishing_link"]):
            return "phishing_link"

        return "generic"

    def analyze(self, message: str, package_name: str = "") -> dict:
        cleaned = self.clean_text(message)
        scam_prob = 0.5

        if self.pipeline:
            try:
                proba = self.pipeline.predict_proba([cleaned])[0]
                scam_prob = float(proba[1])
            except Exception:
                pass

        category = self.classify_category(message, package_name)

        lowered = message.lower()
        if category == "banking_otp" or "otp" in lowered or "kyc" in lowered or "sbi" in lowered:
            scam_prob = max(scam_prob, 0.85)

        verdict = "Scam" if scam_prob >= 0.50 else "Safe"
        confidence = round(scam_prob if verdict == "Scam" else 1 - scam_prob, 3)

        # Severity Assignment Logic:
        # CRITICAL: Only Banking, OTP theft, KYC expiry, UPI fraud, or explicitly dangerous bank phishing
        if verdict == "Scam" and (category in CRITICAL_CATEGORIES or "otp" in lowered or "sbi" in lowered):
            severity = "critical"
        elif verdict == "Scam":
            severity = "moderate"
        else:
            severity = "none"

        return {
            "verdict": verdict,
            "confidence": confidence,
            "category": category,
            "severity": severity,
            "cleaned_text": cleaned,
            "source_app": package_name or "unknown",
            "is_red_alert": severity == "critical"
        }

    def analyze_webpage(self, page_data: dict) -> dict:
        url = page_data.get("url", "")
        title = page_data.get("title", "")
        text = page_data.get("text", "") or page_data.get("html_content", "")
        package_name = page_data.get("package_name", "com.android.chrome")
        has_password_field = bool(page_data.get("has_password_field", False))
        is_http = bool(page_data.get("is_http", False)) or url.startswith("http://")

        combined = f"Title: {title}. URL: {url}. Content: {text[:2000]}"
        base = self.analyze(combined, package_name)

        scam_prob = base["confidence"] if base["verdict"] == "Scam" else (1 - base["confidence"])
        dom_boost = 0.0

        if has_password_field and (is_http or any(t in url.lower() for t in [".xyz", ".top", "verify", "bank-"])):
            dom_boost += 0.50

        total_risk = min(round(scam_prob + dom_boost, 3), 1.0)
        verdict = "Scam" if total_risk >= 0.50 else "Safe"
        confidence = total_risk if verdict == "Scam" else round(1 - total_risk, 3)
        severity = "critical" if (verdict == "Scam" and (confidence >= 0.75 or dom_boost >= 0.40)) else ("moderate" if verdict == "Scam" else "none")

        return {
            "verdict": verdict,
            "confidence": confidence,
            "category": "phishing_link" if verdict == "Scam" else "generic",
            "severity": severity,
            "cleaned_text": self.clean_text(combined),
            "source_app": package_name,
            "is_red_alert": severity == "critical"
        }
