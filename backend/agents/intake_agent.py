"""
Intake & Normalisation Agent.

Responsibilities:
  1. Language detection / validation
  2. STT / OCR stub for voice & photo channels
  3. Gemini-based structured field extraction
  4. Ward resolution via keyword lookup
  5. Authenticity scoring
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from schemas.submission import SubmissionCreate
from utils import gemini_client

logger = logging.getLogger(__name__)

# ── Ward lookup ────────────────────────────────────────────────────────────────
# Maps common Varanasi Cantonment location keywords → ward_id.
# A real deployment would use a PostGIS / BigQuery spatial join.
WARD_LOOKUP: dict[str, str] = {
    # Ward 4 — Sigra & surroundings
    "sigra": "ward_04",
    "sigra marg": "ward_04",
    "shivarampuri": "ward_04",
    "mahmoorganj": "ward_04",
    "vijayalaxmi": "ward_04",
    # Ward 7 — Orderly Bazaar / Cantonment core
    "orderly bazaar": "ward_07",
    "orderly": "ward_07",
    "cantonment": "ward_07",
    "cantt": "ward_07",
    "sadar bazaar": "ward_07",
    "sadar": "ward_07",
    # Ward 11 — Bhelupur / Lanka
    "bhelupur": "ward_11",
    "lanka": "ward_11",
    "durgakund": "ward_11",
    "beniya bagh": "ward_11",
    "beniabagh": "ward_11",
    # Ward 15 — Nadesar / Chetganj
    "nadesar": "ward_15",
    "chetganj": "ward_15",
    "chet singh": "ward_15",
    "kabir chaura": "ward_15",
    "kabirchaura": "ward_15",
    # Ward 18 — Paharia / Shivpur
    "paharia": "ward_18",
    "shivpur": "ward_18",
    "chandpur": "ward_18",
    "pahadiya": "ward_18",
    # Ward 22 — Pandeypur / Lohta
    "pandeypur": "ward_22",
    "lohta": "ward_22",
    "babatpur": "ward_22",
    "pandey pur": "ward_22",
}

_VALID_CATEGORIES = {
    "roads", "water", "health", "education", "sanitation",
    "electricity", "drainage", "housing", "parks", "safety", "anganwadi", "other",
}

_VALID_LANGS = {"en", "hi", "ur", "bho", "mai"}


async def process_submission(raw: SubmissionCreate) -> dict:
    """
    Enrich and normalise a raw citizen submission.

    Steps:
      1. Validate / detect channel & language
      2. For voice/photo channels, treat text as pre-transcribed (MVP stub)
      3. Call Gemini to extract structured fields (category, location, description, sentiment)
      4. Resolve ward_id from location text
      5. Compute authenticity score
      6. Return enriched submission dict (ready for Firestore / BigQuery)

    Returns a dict matching the `Submission` schema (without `id` / `timestamp`,
    which are added by the caller).
    """
    import uuid
    from datetime import datetime, timezone

    submission_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    # ── 1. Channel / text resolution ──────────────────────────────────────────
    text = (raw.text or "").strip()

    if raw.channel in ("voice", "photo") and not text:
        # In production: call STT / OCR here.
        # For MVP, we expect pre-transcribed text in the `text` field.
        text = "[Media content — transcript pending]"
        logger.info("Channel=%s: no text provided, flagged as pending.", raw.channel)

    # ── 2. Language normalisation ─────────────────────────────────────────────
    lang = raw.lang if raw.lang in _VALID_LANGS else "hi"

    # ── 3. Gemini field extraction ────────────────────────────────────────────
    gemini_fields: dict = {}
    if text and text != "[Media content — transcript pending]":
        try:
            gemini_fields = await gemini_client.extract_submission_fields(text, lang)
        except Exception as exc:
            logger.error("Gemini extraction failed: %s", exc)

    # ── 4. Merge / override fields ────────────────────────────────────────────
    # Caller-supplied category takes precedence; Gemini fills gaps.
    category = raw.category
    if category not in _VALID_CATEGORIES:
        category = gemini_fields.get("category", "other")
    if category not in _VALID_CATEGORIES:
        category = "other"

    location = raw.location or gemini_fields.get("location", "Unknown")
    description = gemini_fields.get("description", text[:200])

    # ── 5. Ward resolution ────────────────────────────────────────────────────
    ward_id = _resolve_ward(location)

    # ── 6. Authenticity score ─────────────────────────────────────────────────
    authenticity_score = _compute_authenticity(raw, text)

    enriched = {
        "id": submission_id,
        "timestamp": timestamp,
        "channel": raw.channel,
        "text": text,
        "description": description,
        "category": category,
        "location": location,
        "lang": lang,
        "media_url": raw.media_url,
        "lat": raw.lat,
        "lng": raw.lng,
        "phone_hash": raw.phone_hash,
        "ward_id": ward_id,
        "authenticity_score": authenticity_score,
        "processed": False,
        "cluster_id": None,
        "sentiment": gemini_fields.get("sentiment", "moderate"),
    }

    logger.info(
        "Intake processed submission %s → ward=%s category=%s score=%.2f",
        submission_id,
        ward_id,
        category,
        authenticity_score,
    )
    return enriched


# ── Private helpers ────────────────────────────────────────────────────────────

def _resolve_ward(location: str) -> str:
    """
    Match location text against WARD_LOOKUP keywords (case-insensitive).
    Returns 'ward_unknown' if no match found.
    """
    loc_lower = location.lower()
    for keyword, ward_id in WARD_LOOKUP.items():
        if keyword in loc_lower:
            return ward_id
    return "ward_unknown"


def _compute_authenticity(raw: SubmissionCreate, text: str) -> float:
    """
    Heuristic authenticity score (0.0 – 1.0).

    Base: 0.5
    +0.15  GPS coordinates provided
    +0.15  Text is substantive (>20 chars)
    +0.10  Phone hash provided
    +0.10  Category is specific (not 'other')
    -0.20  Text is empty / too short (<5 chars)
    """
    score = 0.5

    if raw.lat is not None and raw.lng is not None:
        score += 0.15

    if len(text) > 20:
        score += 0.15
    elif len(text) < 5:
        score -= 0.20

    if raw.phone_hash:
        score += 0.10

    if raw.category and raw.category != "other":
        score += 0.10

    return round(max(0.0, min(1.0, score)), 3)
