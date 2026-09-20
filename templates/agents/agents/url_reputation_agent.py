"""
url_reputation_agent.py
-------------------------
Agent 3: URLReputationAgent  (NEW)

Responsibility: look at any URLs inside a message and flag ones that are
commonly used to hide the real destination (link shorteners) or that look
like a misspelled/impersonated brand domain.

This is intentionally rule-based and offline (no external API calls) so it
stays fast and reliable for a live hackathon demo. It works independently
of the ML model — it's a separate, lightweight layer of signal.
"""

import re

KNOWN_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "ow.ly",
    "buff.ly", "cutt.ly", "rebrand.ly", "shorte.st",
}

_SHORTENER_PATTERN = "|".join(re.escape(s) for s in KNOWN_SHORTENERS)
URL_REGEX = re.compile(
    r"(https?://\S+|www\.\S+|\b(?:" + _SHORTENER_PATTERN + r")\S*"
    r"|\b\S+\.(?:com|net|org|xyz|info|biz|co)\S*)",
    re.IGNORECASE,
)

# Common brands that scam links often try to impersonate with lookalike spellings
BRAND_LOOKALIKES = {
    "paypa1": "paypal", "arnaz0n": "amazon", "amaz0n": "amazon",
    "g00gle": "google", "faceb00k": "facebook", "netfl1x": "netflix",
    "0tp": "otp", "bank-verify": "bank",
}


class URLReputationAgent:
    def _extract_urls(self, message: str) -> list:
        return URL_REGEX.findall(message)

    def _get_domain(self, url: str) -> str:
        cleaned = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
        cleaned = re.sub(r"^www\.", "", cleaned, flags=re.IGNORECASE)
        return cleaned.split("/")[0].lower()

    def check(self, message: str) -> dict:
        """
        Returns:
            {
                "has_url": bool,
                "is_shortened": bool,
                "is_lookalike": bool,
                "risk_note": str | None
            }
        """
        urls = self._extract_urls(message)
        if not urls:
            return {
                "has_url": False,
                "is_shortened": False,
                "is_lookalike": False,
                "risk_note": None,
            }

        is_shortened = False
        is_lookalike = False
        notes = []

        for url in urls:
            domain = self._get_domain(url)

            if any(shortener in domain for shortener in KNOWN_SHORTENERS):
                is_shortened = True

            for lookalike, real_brand in BRAND_LOOKALIKES.items():
                if lookalike in domain:
                    is_lookalike = True
                    notes.append(f"domain resembles a fake '{real_brand}' link")

            if domain.count("-") >= 2:
                notes.append("domain has an unusually complex/hyphenated name")

        if is_shortened:
            notes.insert(0, "shortened link detected — real destination is hidden")

        risk_note = "; ".join(dict.fromkeys(notes)) if notes else None

        return {
            "has_url": True,
            "is_shortened": is_shortened,
            "is_lookalike": is_lookalike,
            "risk_note": risk_note,
        }