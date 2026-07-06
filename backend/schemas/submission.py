"""
Pydantic schemas for citizen submissions.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SubmissionCreate(BaseModel):
    """Payload accepted from the citizen-facing frontend."""

    channel: str = Field(..., description="'text' | 'voice' | 'photo'")
    text: str | None = Field(None, description="Free-text complaint / feedback")
    category: str = Field(..., description="Issue category (roads, water, health, …)")
    location: str = Field(..., description="Human-readable location string")
    lang: str = Field("en", description="BCP-47 language code of the input text")
    media_url: str | None = Field(None, description="GCS/CDN URL for voice/photo media")
    lat: float | None = Field(None, description="GPS latitude of reported issue")
    lng: float | None = Field(None, description="GPS longitude of reported issue")
    phone_hash: str | None = Field(
        None, description="SHA-256 hash of citizen phone number for dedup"
    )

    model_config = {"json_schema_extra": {
        "example": {
            "channel": "text",
            "text": "Sigra Marg mein bahut gehre gadde hain, baarish mein paani bhar jaata hai.",
            "category": "roads",
            "location": "Sigra Marg, Ward 4",
            "lang": "hi",
            "lat": 25.3200,
            "lng": 82.9780,
            "phone_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        }
    }}


class Submission(SubmissionCreate):
    """Full submission record stored in Firestore / BigQuery."""

    id: str = Field(..., description="UUID assigned at intake")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
    authenticity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Computed authenticity score 0-1"
    )
    ward_id: str = Field(..., description="Resolved ward identifier, e.g. 'ward_04'")
    processed: bool = Field(False, description="True once the pipeline has run")
