"""
Evidence Fusion Agent.

Responsibilities:
  1. UDISE lookup — nearest school stats from mock_udise.json
  2. Census lookup — ward demographic data from mock_census.json
  3. Google Maps — travel time to nearest referral facility
  4. Development plan overlap check
"""

from __future__ import annotations

import json
import logging
import math
import os
from functools import lru_cache
from pathlib import Path

from utils.maps_client import get_travel_time

logger = logging.getLogger(__name__)

# ── Data paths ─────────────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def _load_udise() -> list[dict]:
    path = _DATA_DIR / "mock_udise.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Could not load mock_udise.json: %s", exc)
        return []


@lru_cache(maxsize=1)
def _load_census() -> dict:
    path = _DATA_DIR / "mock_census.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Could not load mock_census.json: %s", exc)
        return {}


# ── Mock development plan ──────────────────────────────────────────────────────
_MOCK_PLAN: list[dict] = [
    {
        "scheme_name": "Smart City Road Resurfacing Phase-3",
        "categories": ["roads"],
        "wards": ["ward_04", "ward_07"],
        "budget_cr": 12.5,
        "status": "Tendering",
    },
    {
        "scheme_name": "Jal Jeevan Mission — Household Tap Connections",
        "categories": ["water"],
        "wards": ["ward_11", "ward_15", "ward_18"],
        "budget_cr": 8.2,
        "status": "Ongoing",
    },
    {
        "scheme_name": "PM Poshan Shakti Nirman — Anganwadi Upgrades",
        "categories": ["anganwadi", "education"],
        "wards": ["ward_22"],
        "budget_cr": 3.1,
        "status": "Approved",
    },
]

# Nearest referral hospitals (lat/lng) for travel-time calculation
_REFERRAL_HOSPITALS = [
    {"name": "Jayadeva Hospital", "lat": 12.9268, "lng": 77.5946},
    {"name": "NIMHANS", "lat": 12.9373, "lng": 77.5956},
    {"name": "Apollo Hospital Jayanagar", "lat": 12.9221, "lng": 77.5843},
]


async def fetch_evidence(cluster: dict) -> dict:
    """
    Assemble an evidence dict for a need-cluster.

    Returns:
        {
            udise_ref: str | None,
            census_ref: str | None,
            maps_ref: str | None,
            plan_ref: str | None,
            need_gap_value: float,        # used by scoring_agent (G component)
            vulnerability_index: float,   # used by scoring_agent (V component)
            travel_minutes: float,        # used by scoring_agent (F component)
            plan_overlap: float,          # 0 | 0.5 | 1.0 (used by scoring_agent O)
        }
    """
    ward_id = cluster.get("ward_id", "ward_unknown")
    category = cluster.get("category", "other")
    lat = cluster.get("lat", 12.9716)
    lng = cluster.get("lng", 77.5946)

    # ── UDISE ─────────────────────────────────────────────────────────────────
    udise_ref, need_gap_value = _udise_lookup(ward_id, lat, lng, category)

    # ── Census ────────────────────────────────────────────────────────────────
    census_ref, vulnerability_index = _census_lookup(ward_id)

    # ── Travel time to nearest facility ───────────────────────────────────────
    maps_ref, travel_minutes = await _maps_lookup(lat, lng)

    # ── Development plan overlap ──────────────────────────────────────────────
    plan_ref, plan_overlap = _plan_overlap(ward_id, category)

    return {
        "udise_ref": udise_ref,
        "census_ref": census_ref,
        "maps_ref": maps_ref,
        "plan_ref": plan_ref,
        "need_gap_value": need_gap_value,
        "vulnerability_index": vulnerability_index,
        "travel_minutes": travel_minutes,
        "plan_overlap": plan_overlap,
    }


# ── Private helpers ────────────────────────────────────────────────────────────

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _udise_lookup(ward_id: str, lat: float, lng: float, category: str) -> tuple[str | None, float]:
    """
    Find the nearest school in mock_udise.json.
    Returns (citation_string, need_gap_value 0-1).
    need_gap_value is computed as: max(0, (enrollment - capacity) / capacity)
    """
    schools = _load_udise()
    if not schools:
        return None, 0.5

    # Filter by ward first; if no match, use all schools
    ward_schools = [s for s in schools if s.get("ward_id") == ward_id]
    pool = ward_schools if ward_schools else schools

    nearest = min(pool, key=lambda s: _haversine_km(lat, lng, s["lat"], s["lng"]))

    enrollment = nearest.get("enrollment", 0)
    capacity = nearest.get("seat_capacity", 1)
    teacher_count = nearest.get("teacher_count", 1)
    condition = nearest.get("building_condition", "unknown")

    # Need gap: overcrowding ratio (capped at 1.0)
    gap = max(0.0, (enrollment - capacity) / max(capacity, 1))
    gap = min(gap, 1.0)

    # Boost for poor building condition
    if condition == "poor":
        gap = min(gap + 0.2, 1.0)
    elif condition == "fair":
        gap = min(gap + 0.1, 1.0)

    citation = (
        f"UDISE+ {nearest['school_id']} — {nearest['name']} "
        f"(Enrollment {enrollment} vs Capacity {capacity}, "
        f"{teacher_count} teachers, building: {condition})"
    )
    return citation, round(gap, 3)


def _census_lookup(ward_id: str) -> tuple[str | None, float]:
    """
    Retrieve ward demographics from mock_census.json.
    Returns (citation_string, vulnerability_index 0-1).
    """
    census = _load_census()
    ward = census.get(ward_id)
    if not ward:
        return None, 0.5

    vi = ward.get("vulnerability_index", 0.5)
    bpl = ward.get("below_poverty_line", 0.0)
    sc_st = ward.get("sc_st_percent", 0.0)
    pop = ward.get("population", 0)
    lit = ward.get("literacy_rate", 0.0)

    citation = (
        f"{ward_id} — Pop: {pop:,}, Literacy: {int(lit*100)}%, "
        f"Vulnerability index: {vi:.2f}, BPL: {int(bpl*100)}%, SC/ST: {int(sc_st*100)}%"
    )
    return citation, round(vi, 3)


async def _maps_lookup(lat: float, lng: float) -> tuple[str | None, float]:
    """
    Calculate travel time to the nearest referral facility.
    Returns (citation_string, travel_minutes).
    """
    nearest_fac = min(
        _REFERRAL_HOSPITALS,
        key=lambda f: _haversine_km(lat, lng, f["lat"], f["lng"]),
    )

    travel_data = await get_travel_time(lat, lng, nearest_fac["lat"], nearest_fac["lng"])
    km = travel_data.get("distance_km", 0.0)
    mins = travel_data.get("duration_minutes", 0.0)
    mode = travel_data.get("status", "MOCK")

    citation = (
        f"Nearest facility: {nearest_fac['name']} — "
        f"{km:.1f} km, {mins:.0f} min by road ({mode})"
    )
    return citation, mins


def _plan_overlap(ward_id: str, category: str) -> tuple[str | None, float]:
    """
    Check for active scheme overlap in the development plan.
    Returns (citation_string, overlap_penalty 0/0.5/1.0).
    """
    overlapping = [
        p for p in _MOCK_PLAN
        if ward_id in p.get("wards", []) and category in p.get("categories", [])
    ]

    if not overlapping:
        return "No overlapping active scheme found in 2025-26 district plan.", 0.0

    scheme = overlapping[0]
    status = scheme.get("status", "Unknown")

    if status in ("Ongoing", "Approved"):
        penalty = 1.0
        citation = (
            f"⚠ Overlap: {scheme['scheme_name']} (Status: {status}, "
            f"Budget: ₹{scheme['budget_cr']} Cr) — duplication risk HIGH"
        )
    elif status == "Tendering":
        penalty = 0.5
        citation = (
            f"△ Partial overlap: {scheme['scheme_name']} (Status: {status}) — "
            f"coordinate before proceeding"
        )
    else:
        penalty = 0.0
        citation = f"Proposed scheme: {scheme['scheme_name']} (Status: {status})"

    return citation, penalty
