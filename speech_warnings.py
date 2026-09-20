"""
speech_warnings.py
-------------------
Multi-Lingual Dual Voice Warning System
Provides fallback spoken warning scripts and BCP-47 codes.
"""

WARNING_TEXT = {
    "en": {
        "local": "Emergency Warning! This page or message is a dangerous scam. Do not enter any passwords or click any links.",
        "english": "Emergency Warning! This page or message is a dangerous scam. Do not enter any passwords or click any links."
    },
    "hi": {
        "local": "आपातकालीन चेतावनी! यह पेज या संदेश एक खतरनाक धोखाधड़ी है। कृपया तुरंत पीछे हटें और कोई पासवर्ड दर्ज न करें।",
        "english": "Emergency Warning! Fraudulent webpage detected. Do not enter any passwords or credit card details."
    },
    "pa": {
        "local": "ਐਮਰਜੈਂਸੀ ਚੇਤਾਵਨੀ! ਇਹ ਪੰਨਾ ਜਾਂ ਸੁਨੇਹਾ ਇੱਕ ਖਤਰਨਾਕ ਧੋਖਾਧੜੀ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਕੋਈ ਵੀ ਪਾਸਵਰਡ ਦਰਜ ਨਾ ਕਰੋ।",
        "english": "Emergency Warning! Fraudulent webpage detected. Do not enter any passwords or credit card details."
    },
    "bn": {
        "local": "জরুরী সতর্কতা! এই পৃষ্ঠা বা বার্তাটি একটি বিপজ্জনক প্রতারণা। কোন পাসওয়ার্ড বা পিন প্রবেশ করবেন না।",
        "english": "Emergency Warning! Fraudulent webpage detected. Do not enter any passwords or credit card details."
    },
    "ta": {
        "local": "அவசர எச்சரிக்கை! இந்த பக்கம் அல்லது செய்தி ஒரு ஆபத்தான மோசடி. கடவுச்சொற்களை உள்ளிட வேண்டாம்.",
        "english": "Emergency Warning! Fraudulent webpage detected. Do not enter any passwords or credit card details."
    },
    "te": {
        "local": "అత్యవసర హెచ్చరిక! ఈ పేజీ లేదా సందేశం ప్రమాదకరమైన మోసం. పాస్‌వర్డ్‌లను నమోదు చేయవద్దు.",
        "english": "Emergency Warning! Fraudulent webpage detected. Do not enter any passwords or credit card details."
    },
    "mr": {
        "local": "आणीबाणीचा इशारा! हे पान किंवा संदेश एक धोकादायक फसवणूक आहे. कोणताही पासवर्ड टाकू नका.",
        "english": "Emergency Warning! Fraudulent webpage detected. Do not enter any passwords or credit card details."
    },
    "gu": {
        "local": "ઇમરજન્સી ચેતવણી! આ પૃષ્ઠ અથવા સંદેશ એક ખતરનાક કૌભાંડ છે. કોઈપણ પાસવર્ડ દાખલ કરશો નહીં.",
        "english": "Emergency Warning! Fraudulent webpage detected. Do not enter any passwords or credit card details."
    },
    "kn": {
        "local": "ತುರ್ತು ಎಚ್ಚರಿಕೆ! ಈ ಪುಟ ಅಥವಾ ಸಂದೇಶವು ಅಪಾಯಕಾರಿ ವಂಚನೆಯಾಗಿದೆ. ಯಾವುದೇ ಪಾಸ್‌ವರ್ಡ್ ನಮೂದಿಸಬೇಡಿ.",
        "english": "Emergency Warning! Fraudulent webpage detected. Do not enter any passwords or credit card details."
    },
    "ml": {
        "local": "അടിയന്തിര മുന്നറിയിപ്പ്! ഈ പേജോ സന്ദേശമോ ഒരു അപകടകരമായ തട്ടിപ്പാണ്. പാസ്‌വേഡുകൾ നൽകരുത്.",
        "english": "Emergency Warning! Fraudulent webpage detected. Do not enter any passwords or credit card details."
    },
    "es": {
        "local": "¡Advertencia de emergencia! Esta página o mensaje es una estafa peligrosa. No ingrese ninguna contraseña.",
        "english": "Emergency Warning! Fraudulent webpage detected. Do not enter any passwords or credit card details."
    },
    "fr": {
        "local": "Alerte d'urgence! Cette page ou ce message est une arnaque dangereuse. Ne saisissez aucun mot de passe.",
        "english": "Emergency Warning! Fraudulent webpage detected. Do not enter any passwords or credit card details."
    },
}

LANG_BCP47 = {
    "en": "en-US", "hi": "hi-IN", "hinglish": "hi-IN", "pa": "pa-IN",
    "bn": "bn-IN", "ta": "ta-IN", "te": "te-IN", "mr": "mr-IN",
    "gu": "gu-IN", "kn": "kn-IN", "ml": "ml-IN", "es": "es-ES",
    "fr": "fr-FR",
}


def get_spoken_warning(lang_code: str = "en") -> dict:
    lang_code = (lang_code or "en").lower()[:2]
    data = WARNING_TEXT.get(lang_code, WARNING_TEXT["en"])
    speech_lang = LANG_BCP47.get(lang_code, "en-US")
    return {
        "text_local": data["local"],
        "text_english": data["english"],
        "speech_lang": speech_lang,
    }
