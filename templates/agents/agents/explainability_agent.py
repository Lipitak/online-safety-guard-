"""
explainability_agent.py
------------------------
Agent 2: ExplainabilityAgent

Responsibility: given a message and the DetectionAgent's verdict, explain
WHY in plain language — rule-based quick flags (link, urgency language)
plus SHAP-based top contributing words when the verdict is "Scam".

This agent does not classify anything itself; it only explains a
classification that was already made (separation of concerns).
"""

import re
import shap


URL_PATTERN = re.compile(r"http\S+|www\S+|bit\.ly\S*")
URGENCY_WORDS = {
    "urgent", "immediately", "verify", "suspend", "blocked", "act now",
    "click here", "limited time", "winner", "congratulations", "otp",
    "account will be", "final notice", "expire",
}


class ExplainabilityAgent:
    def __init__(self, pipeline, clean_text_fn):
        """
        pipeline: the same sklearn Pipeline used by DetectionAgent
        clean_text_fn: the same text-cleaning function DetectionAgent uses,
                        so SHAP explanations are computed on identically
                        preprocessed text
        """
        self.pipeline = pipeline
        self.clean_text = clean_text_fn

        def predict_proba_wrapper(texts):
            cleaned = [self.clean_text(t) for t in texts]
            return self.pipeline.predict_proba(cleaned)

        masker = shap.maskers.Text(tokenizer=r"\W+")
        self.explainer = shap.Explainer(
            predict_proba_wrapper, masker, output_names=["Safe", "Scam"]
        )

    def _detect_flags(self, raw_message: str) -> list:
        flags = []
        if URL_PATTERN.search(raw_message.lower()):
            flags.append("contains a link")
        lowered = raw_message.lower()
        if any(word in lowered for word in URGENCY_WORDS):
            flags.append("uses urgent/pressure language")
        return flags

    def _top_shap_words(self, cleaned_message: str, top_n=3) -> list:
        shap_values = self.explainer([cleaned_message])
        words = shap_values.data[0]
        scam_scores = shap_values.values[0][:, 1]  # contribution to "Scam" class
        ranked = sorted(zip(words, scam_scores), key=lambda x: x[1], reverse=True)
        return [w.strip() for w, score in ranked if score > 0 and w.strip()][:top_n]

    def explain(self, raw_message: str, cleaned_message: str, verdict: str) -> dict:
        """
        Returns:
            {
                "reason": str,          # human-readable explanation
                "top_words": list[str], # SHAP top contributing words (only if Scam)
            }
        """
        reason_parts = self._detect_flags(raw_message)
        top_words = []

        if verdict == "Scam":
            try:
                top_words = self._top_shap_words(cleaned_message, top_n=3)
                if top_words:
                    reason_parts.append(f"suspicious phrases: {', '.join(top_words)}")
            except Exception:
                pass  # fail gracefully in a live demo; rule-based flags still show

        if not reason_parts:
            reason_parts.append(
                "no strong scam indicators found" if verdict == "Safe"
                else "unusual word patterns detected"
            )

        return {
            "reason": "; ".join(reason_parts),
            "top_words": top_words,
        }
    