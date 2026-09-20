"""
url_reputation_agent.py
-------------------------
Agent 3: URLReputationAgent (ScamShield SIH Project)
Integrates Google Safe Browsing API, VirusTotal API, and local heuristic fallback.
"""

import os
import re
import math
import requests
from urllib.parse import urlparse

SAFE_BROWSING_API_KEY = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY", "")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")

# 1. Known URL Shorteners
KNOWN_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "ow.ly",
    "buff.ly", "cutt.ly", "rebrand.ly", "shorte.st", "v.gd", "clck.ru",
    "rotf.lol", "tiny.cc", "rb.gy", "shorturl.at", "s.id", "kutt.it"
}

# 2. High-Risk Scam & Phishing Top Level Domains (TLDs)
HIGH_RISK_TLDS = {
    "xyz", "top", "tk", "ml", "ga", "cf", "gq", "online", "site",
    "vip", "work", "click", "biz", "download", "racing", "cam",
    "monster", "fit", "rest", "icu", "link", "stream", "space",
    "club", "fun", "pw", "cc", "top", "cfd", "shop"
}

# 3. Protected Brand Directory (Major Indian Banks, Fintech, & Global Platforms)
PROTECTED_BRANDS = {
    "sbi": "State Bank of India",
    "statebankofindia": "State Bank of India",
    "hdfc": "HDFC Bank",
    "hdfcbank": "HDFC Bank",
    "icici": "ICICI Bank",
    "icicibank": "ICICI Bank",
    "axisbank": "Axis Bank",
    "kotak": "Kotak Mahindra Bank",
    "pnb": "Punjab National Bank",
    "paytm": "Paytm",
    "phonepe": "PhonePe",
    "gpay": "Google Pay",
    "bhim": "BHIM UPI",
    "razorpay": "Razorpay",
    "paypal": "PayPal",
    "amazon": "Amazon",
    "google": "Google",
    "gmail": "Google Gmail",
    "microsoft": "Microsoft",
    "outlook": "Microsoft Outlook",
    "apple": "Apple",
    "icloud": "Apple iCloud",
    "facebook": "Meta Facebook",
    "instagram": "Instagram",
    "whatsapp": "WhatsApp",
    "netflix": "Netflix",
    "telegram": "Telegram",
    "naukri": "Naukri Job Portal",
    "linkedin": "LinkedIn",
}

HOMOGRAPH_MAP = {
    '0': 'o', '1': 'i', 'l': 'i', '3': 'e', '4': 'a',
    '@': 'a', '5': 's', '8': 'b', '$': 's', 'vv': 'w'
}

SENSITIVE_KEYWORDS = [
    "login", "verify", "verification", "kyc", "account", "update",
    "banking", "secure", "otp", "wallet", "claim", "reward", "winner",
    "payout", "refund", "password", "credential", "session"
]

_SHORTENER_PATTERN = "|".join(re.escape(s) for s in KNOWN_SHORTENERS)
URL_REGEX = re.compile(
    r"(https?://\S+|www\.\S+|\b(?:" + _SHORTENER_PATTERN + r")\S*"
    r"|\b[a-zA-Z0-9.-]+\.(?:com|net|org|in|co|xyz|info|biz|top|online|site|app|io|tech|me|vip|work|click)\b\S*)",
    re.IGNORECASE,
)


def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def normalize_homograph(text: str) -> str:
    res = text.lower()
    for char, replacement in HOMOGRAPH_MAP.items():
        res = res.replace(char, replacement)
    return res


def calculate_entropy(text: str) -> float:
    if not text:
        return 0.0
    entropy = 0.0
    for x in set(text):
        p_x = float(text.count(x)) / len(text)
        entropy -= p_x * math.log(p_x, 2)
    return round(entropy, 2)


class URLReputationAgent:
    def _extract_urls(self, text: str) -> list:
        found = URL_REGEX.findall(text)
        cleaned = []
        for u in found:
            u = u.rstrip(".,;!)'\">")
            if u and u not in cleaned:
                cleaned.append(u)
        return cleaned

    def _parse_url_components(self, url: str):
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        parsed = urlparse(url)
        hostname = parsed.netloc.split(":")[0].lower()
        if hostname.startswith("www."):
            hostname = hostname[4:]
        path = parsed.path.lower() + "?" + parsed.query.lower()
        return hostname, path

    def _check_google_safe_browsing(self, url: str) -> dict:
        if not SAFE_BROWSING_API_KEY:
            return {"api_flagged": False, "note": None}
        try:
            api_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={SAFE_BROWSING_API_KEY}"
            payload = {
                "client": {"clientId": "ScamShield", "clientVersion": "4.0.0"},
                "threatInfo": {
                    "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": url}]
                }
            }
            resp = requests.post(api_url, json=payload, timeout=2.0)
            if resp.status_code == 200:
                data = resp.json()
                if data and "matches" in data and len(data["matches"]) > 0:
                    threat = data["matches"][0].get("threatType", "SOCIAL_ENGINEERING")
                    return {"api_flagged": True, "note": f"Google Safe Browsing flagged URL as {threat}"}
        except Exception as e:
            print("Google Safe Browsing API Timeout/Error:", e)
        return {"api_flagged": False, "note": None}

    def _check_virustotal(self, url: str) -> dict:
        if not VIRUSTOTAL_API_KEY:
            return {"api_flagged": False, "note": None}
        try:
            import base64
            url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
            headers = {"x-apikey": VIRUSTOTAL_API_KEY}
            resp = requests.get(f"https://www.virustotal.com/api/v3/urls/{url_id}", headers=headers, timeout=2.5)
            if resp.status_code == 200:
                stats = resp.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                if malicious > 0:
                    return {"api_flagged": True, "note": f"VirusTotal flagged URL by {malicious} security vendors"}
        except Exception as e:
            print("VirusTotal API Timeout/Error:", e)
        return {"api_flagged": False, "note": None}

    def analyze_single_url(self, url: str) -> dict:
        hostname, path = self._parse_url_components(url)
        notes = []
        is_shortened = False
        is_lookalike = False
        is_ip = False
        suspicious_tld = False
        impersonated_brand = None
        risk_score = 0.0

        # 1. API Verification
        gsb_res = self._check_google_safe_browsing(url)
        if gsb_res["api_flagged"]:
            risk_score += 0.95
            notes.append(gsb_res["note"])

        vt_res = self._check_virustotal(url)
        if vt_res["api_flagged"]:
            risk_score += 0.90
            notes.append(vt_res["note"])

        # 2. Check IP Hostname
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname):
            is_ip = True
            risk_score += 0.85
            notes.append("URL uses a raw IP address instead of a domain name")

        # 3. Check Shorteners
        if any(shortener in hostname for shortener in KNOWN_SHORTENERS):
            is_shortened = True
            risk_score += 0.30
            notes.append("shortened link detected — real destination URL is hidden")

        # 4. Check TLD
        parts = hostname.split(".")
        tld = parts[-1] if len(parts) > 1 else ""
        if tld in HIGH_RISK_TLDS:
            suspicious_tld = True
            risk_score += 0.35
            notes.append(f"high-risk top-level domain '.{tld}' commonly used in fraud")

        # 5. Check Subdomains & Hyphens
        domain_without_tld = ".".join(parts[:-1]) if len(parts) > 1 else hostname
        if hostname.count("-") >= 2:
            risk_score += 0.25
            notes.append("suspicious hyphenated domain structure designed to mimic official portals")

        if len(parts) >= 4:
            risk_score += 0.25
            notes.append("excessive subdomains used to mask actual domain identity")

        # 6. Typosquatting & Brand Spoofing (Skip known shorteners like bit.ly)
        if not is_shortened:
            norm_domain = normalize_homograph(domain_without_tld)
            for brand_key, brand_name in PROTECTED_BRANDS.items():
                if brand_key in norm_domain:
                    if norm_domain not in [brand_key, f"www.{brand_key}"]:
                        is_lookalike = True
                        impersonated_brand = brand_name
                        risk_score += 0.75
                        notes.append(f"fake link impersonating official brand '{brand_name}'")
                        break
                else:
                    for domain_chunk in norm_domain.replace("-", ".").split("."):
                        if 4 <= len(domain_chunk) <= 18:
                            dist = levenshtein_distance(domain_chunk, brand_key)
                            if 1 <= dist <= 2 and len(brand_key) >= 5:
                                is_lookalike = True
                                impersonated_brand = brand_name
                                risk_score += 0.80
                                notes.append(f"typosquatted domain '{domain_chunk}' mimicking '{brand_name}'")
                                break
                if is_lookalike:
                    break

        # 7. Domain Entropy
        entropy = calculate_entropy(domain_without_tld)
        if entropy > 3.85 and len(domain_without_tld) > 8 and not is_lookalike and not is_shortened:
            risk_score += 0.30
            notes.append(f"high-entropy random domain name detected (entropy score: {entropy})")

        # 8. Path Trigger Keywords
        found_keywords = [kw for kw in SENSITIVE_KEYWORDS if kw in path or (not is_shortened and kw in norm_domain)]
        if found_keywords and (is_lookalike or suspicious_tld or is_shortened or is_ip or risk_score >= 0.3):
            risk_score += 0.20
            notes.append(f"sensitive path triggers found: {', '.join(found_keywords)}")

        final_risk = min(round(risk_score, 2), 1.0)
        verdict = "Dangerous" if final_risk >= 0.50 else ("Suspicious" if final_risk >= 0.30 else "Clean")

        return {
            "url": url,
            "domain": hostname,
            "verdict": verdict,
            "risk_score": final_risk,
            "is_shortened": is_shortened,
            "is_lookalike": is_lookalike,
            "is_ip": is_ip,
            "suspicious_tld": suspicious_tld,
            "impersonated_brand": impersonated_brand,
            "notes": notes,
        }

    def check(self, message_or_url: str) -> dict:
        urls = self._extract_urls(message_or_url)
        if not urls:
            return {
                "has_url": False,
                "urls_found": 0,
                "is_shortened": False,
                "is_lookalike": False,
                "is_dangerous": False,
                "max_risk_score": 0.0,
                "risk_note": None,
                "details": [],
            }

        analyzed_urls = [self.analyze_single_url(u) for u in urls]
        max_risk = max(a["risk_score"] for a in analyzed_urls)
        is_shortened = any(a["is_shortened"] for a in analyzed_urls)
        is_lookalike = any(a["is_lookalike"] for a in analyzed_urls)
        # Fix: is_dangerous is True only when verdict is "Dangerous" (risk_score >= 0.50)
        is_dangerous = any(a["verdict"] == "Dangerous" for a in analyzed_urls)

        all_notes = []
        for a in analyzed_urls:
            all_notes.extend(a["notes"])

        unique_notes = list(dict.fromkeys(all_notes))
        risk_note = "; ".join(unique_notes) if unique_notes else None

        return {
            "has_url": True,
            "urls_found": len(urls),
            "is_shortened": is_shortened,
            "is_lookalike": is_lookalike,
            "is_dangerous": is_dangerous,
            "max_risk_score": max_risk,
            "risk_note": risk_note,
            "details": analyzed_urls,
        }