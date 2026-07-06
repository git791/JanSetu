"""
Google Gemini client wrapper.

Uses `google-generativeai` SDK.  All public functions gracefully return
sensible defaults if the API key is missing or the call fails — so the
app can still run locally without a Gemini key.
"""

from __future__ import annotations

import json
import logging
import os
import re

logger = logging.getLogger(__name__)

# ── Lazy initialisation ───────────────────────────────────────────────────────
_model_flash = None
_model_vision = None
_GEMINI_AVAILABLE = False


def _init_gemini() -> None:
    global _model_flash, _model_vision, _GEMINI_AVAILABLE

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set — Gemini client running in stub mode.")
        return

    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=api_key)
        _model_flash = genai.GenerativeModel("gemini-3.5-flash")
        _model_vision = genai.GenerativeModel("gemini-3.5-flash")
        _GEMINI_AVAILABLE = True
        logger.info("Gemini client initialised (gemini-1.5-flash).")
    except Exception as exc:
        logger.warning("Failed to init Gemini: %s — running in stub mode.", exc)


_init_gemini()


# ── Public helpers ────────────────────────────────────────────────────────────

async def extract_submission_fields(text: str, lang: str = "en") -> dict:
    """
    Use Gemini Flash to extract structured fields from free-form complaint text.

    Returns a dict with keys: category, location, description, sentiment.
    Falls back to heuristic defaults if Gemini is unavailable.
    """
    if not _GEMINI_AVAILABLE or _model_flash is None:
        return _heuristic_extract(text)

    prompt = f"""You are a municipal complaint categorisation assistant for Bangalore, India.
Extract the following fields from the citizen complaint below and respond ONLY with valid JSON.

Fields to extract:
- category: one of [roads, water, health, education, sanitation, electricity, drainage, housing, parks, safety, anganwadi, other]
- location: specific place name or street mentioned
- description: one-sentence English summary of the issue
- sentiment: one of [urgent, moderate, low]

Complaint (language: {lang}):
\"\"\"{text}\"\"\"

Respond with JSON only, no markdown fences."""

    try:
        response = _model_flash.generate_content(prompt)
        raw = response.text.strip()
        # Strip potential markdown code fences
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        result = json.loads(raw)
        return result
    except Exception as exc:
        logger.error("extract_submission_fields error: %s", exc)
        return _heuristic_extract(text)


async def ocr_image(image_bytes: bytes) -> str:
    """
    Send an image to Gemini multimodal model and return extracted text/description.
    Falls back to a placeholder if Gemini is unavailable.
    """
    if not _GEMINI_AVAILABLE or _model_vision is None:
        return "The image shows a broken, hanging street light on a main road in Bangalore South. The wires are exposed and it looks dangerous."

    try:
        import google.generativeai as genai  # type: ignore

        image_part = {"mime_type": "image/jpeg", "data": image_bytes}
        prompt = (
            "Describe this image in detail, focusing on any visible civic issues "
            "such as road damage, waterlogging, broken infrastructure, etc. "
            "Also extract any visible text."
        )
        response = _model_vision.generate_content([prompt, image_part])
        return response.text.strip()
    except Exception as exc:
        logger.error("ocr_image error: %s", exc)
        return "[Image OCR failed]"


async def translate_to_english(text: str, source_lang: str = "hi") -> str:
    """
    Translate text to English using Gemini as a fallback translator.
    Returns the original text unchanged if Gemini is unavailable.
    """
    if source_lang == "en":
        return text

    if not _GEMINI_AVAILABLE or _model_flash is None:
        return text  # Return original — frontend can handle multilingual display

    prompt = (
        f"Translate the following {source_lang} text to English. "
        f"Return ONLY the translated text, no explanations.\n\n{text}"
    )

    try:
        response = _model_flash.generate_content(prompt)
        return response.text.strip()
    except Exception as exc:
        logger.error("translate_to_english error: %s", exc)
        return text


# ── Private helpers ───────────────────────────────────────────────────────────

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "roads": ["road", "sadak", "pothole", "gadda", "marg", "footpath", "traffic"],
    "water": ["water", "paani", "pani", "supply", "tap", "nala", "pipeline"],
    "health": ["health", "hospital", "doctor", "medicine", "dawai", "clinic", "nurse"],
    "education": ["school", "vidyalaya", "teacher", "shiksha", "students", "class", "roof"],
    "sanitation": ["toilet", "shauchalay", "garbage", "kachra", "drainage", "sewage"],
    "electricity": ["light", "bijli", "electricity", "power", "streetlight", "wire"],
    "drainage": ["drain", "naali", "flood", "baarish", "waterlog", "overflow"],
    "housing": ["house", "ghar", "shelter", "colony", "slum"],
    "parks": ["park", "garden", "udyan", "playground", "ground"],
    "safety": ["safety", "suraksha", "crime", "dark", "cctv", "police"],
    "anganwadi": ["anganwadi", "child", "baccha", "nutrition", "poshan"],
}


def _heuristic_extract(text: str) -> dict:
    """Simple keyword-based category extraction used when Gemini is unavailable."""
    text_lower = text.lower()
    detected_category = "other"
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            detected_category = cat
            break

    # Sentiment heuristic
    urgent_words = ["urgent", "emergency", "immediate", "bahut", "abhi", "jaldi"]
    sentiment = "urgent" if any(w in text_lower for w in urgent_words) else "moderate"

    return {
        "category": detected_category,
        "location": "Unknown location",
        "description": text[:200] if text else "No description",
        "sentiment": sentiment,
    }
