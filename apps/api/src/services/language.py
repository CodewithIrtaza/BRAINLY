"""
Brainly API - Language Detection Service

Detect Urdu, Roman Urdu, and English.
"""
from typing import Literal
from langdetect import detect, LangDetectException


LanguageCode = Literal["en", "ur", "ur-Roman"]


def detect_language(text: str) -> LanguageCode:
    """
    Detect language of input text.

    Returns one of: en, ur, ur-Roman
    """
    if not text or not text.strip():
        return "en"

    try:
        # langdetect returns ISO 639-1 codes
        lang = detect(text)

        if lang == "ur":
            # Check if it's Roman Urdu (Latin script) vs Urdu script
            if _is_roman_urdu(text):
                return "ur-Roman"
            return "ur"
        elif lang == "en":
            return "en"
        else:
            # Default to English for other languages
            return "en"
    except LangDetectException:
        return "en"


def _is_roman_urdu(text: str) -> bool:
    """
    Heuristic to detect Roman Urdu (Latin script) vs Urdu script.

    Roman Urdu uses Latin characters with Urdu words.
    Urdu script uses Arabic/Persian characters.
    """
    # Check for Urdu script characters (Arabic block)
    urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F')
    latin_chars = sum(1 for c in text if 'a' <= c.lower() <= 'z')

    # If mostly Urdu script chars, it's Urdu (not Roman)
    total = urdu_chars + latin_chars
    if total == 0:
        return True

    # If more than 30% Urdu script, likely Urdu script (not Roman Urdu)
    if urdu_chars / total > 0.3:
        return False

    # Check for common Roman Urdu words
    roman_urdu_words = {
        "hai", "hain", "ho", "kya", "kaise", "kahan", "kab", "kyun",
        "mein", "ko", "se", "ka", "ke", "ki", "aur", "ya", "nahi",
        "han", "ji", "theek", "acha", "bahut", "zaroor", "shukriya",
        "kripya", "madad", "chahiye", "chahte", "mil", "sakta",
    }

    words = text.lower().split()
    roman_count = sum(1 for w in words if w in roman_urdu_words)

    if len(words) > 0 and roman_count / len(words) > 0.1:
        return True

    return True  # Default to Roman Urdu for Latin script


def get_language_name(code: LanguageCode) -> str:
    """Get human-readable language name."""
    names = {
        "en": "English",
        "ur": "Urdu",
        "ur-Roman": "Roman Urdu",
    }
    return names.get(code, "English")


def validate_language(code: str) -> LanguageCode:
    """Validate and normalize language code."""
    valid = {"en", "ur", "ur-Roman", "auto"}
    if code not in valid:
        return "en"
    return code  # type: ignore