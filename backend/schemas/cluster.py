"""
Pydantic schemas for need-clusters and scoring.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """Explainable components of the priority score (all 0-1)."""

    D: float = Field(..., ge=0.0, le=1.0, description="Demand Intensity")
    G: float = Field(..., ge=0.0, le=1.0, description="Need Gap")
    V: float = Field(..., ge=0.0, le=1.0, description="Vulnerability Index")
    F: float = Field(..., ge=0.0, le=1.0, description="Feasibility")
    O: float = Field(..., ge=0.0, le=1.0, description="Overlap Penalty")


class Evidence(BaseModel):
    """Human-readable citations used during scoring."""

    udise_ref: str | None = Field(None, description="Nearest school UDISE citation")
    census_ref: str | None = Field(None, description="Ward census citation")
    maps_ref: str | None = Field(None, description="Distance / travel-time citation")
    plan_ref: str | None = Field(None, description="Development plan overlap note")
    earth_engine_ref: str | None = Field(
        None, description="Google Earth Engine NDVI / flood citation"
    )


class NeedCluster(BaseModel):
    """Aggregated need-cluster derived from one or more citizen submissions."""

    id: str
    name: str
    category: str
    ward_id: str
    location: str
    demand_count: int = Field(..., ge=1)
    priority_score: float = Field(..., ge=0.0, le=100.0)
    score_breakdown: ScoreBreakdown
    evidence: Evidence
    cost_estimate: float = Field(..., description="Estimated cost in lakhs INR")
    beneficiaries: int
    status: str = Field(
        ...,
        description="Received | Under Review | Approved | In Progress | Completed",
    )
    lat: float
    lng: float
    last_updated: str = Field(..., description="ISO-8601 UTC timestamp")
    submission_ids: list[str] = Field(default_factory=list)

    # Extra field returned by scoring agent — not stored in DB schema
    citation_cards: list[dict] | None = Field(
        None, description="Explainability cards per score factor"
    )

    model_config = {"json_schema_extra": {
        "example": {
            "id": "cluster_ward07_edu_001",
            "name": "Govt Primary School Sigra — Roof Leak & Seat Shortage",
            "category": "education",
            "ward_id": "ward_07",
            "location": "Sigra, Varanasi Cantonment",
            "demand_count": 214,
            "priority_score": 87.0,
            "score_breakdown": {"D": 0.95, "G": 0.82, "V": 0.68, "F": 0.74, "O": 0.0},
            "evidence": {
                "udise_ref": "UDISE+ U09130101001 — Govt Primary Sigra (enrollment 612 vs capacity 440)",
                "census_ref": "Ward 07 — vulnerability index 0.68, BPL 31%",
                "maps_ref": "Nearest hospital 4.2 km, 18 min (Google Maps)",
                "plan_ref": "No overlapping scheme in 2025-26 district plan",
            },
            "cost_estimate": 12.5,
            "beneficiaries": 612,
            "status": "Under Review",
            "lat": 25.312,
            "lng": 82.9847,
            "last_updated": "2025-07-01T10:00:00Z",
            "submission_ids": [],
        }
    }}
