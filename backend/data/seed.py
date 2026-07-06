"""
Data seeding script for JanSetu MVP.

Usage:
    python data/seed.py

Steps:
  1. Load synthetic_submissions.json
  2. Run each through the full pipeline: intake → dedup → evidence → scoring
  3. Save to BigQuery (or in-memory fallback)
  4. Pre-seed 12 canonical NeedClusters for fast demo start
  5. Print summary
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the parent directory to sys.path so we can import backend modules
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(_BACKEND_DIR / ".env")

from agents.dedup_agent import find_or_create_cluster
from agents.evidence_agent import fetch_evidence
from agents.intake_agent import process_submission
from agents.scoring_agent import compute_priority_score
from schemas.submission import SubmissionCreate
from utils.bigquery_client import (
    get_in_memory_clusters,
    init_bigquery,
    save_cluster,
    save_submission,
)
from utils.firestore_client import init_firestore, save_cluster_realtime, save_submission_realtime

_DATA_DIR = Path(__file__).resolve().parent

# ── Pre-computed canonical clusters ───────────────────────────────────────────

CANONICAL_CLUSTERS = [
    {
        "id": "cluster_ward07_edu_001",
        "name": "Govt Primary School Sigra — Roof Leak & Seat Shortage",
        "category": "education",
        "ward_id": "ward_07",
        "location": "Sigra, Varanasi Cantonment",
        "demand_count": 214,
        "priority_score": 87.0,
        "score_breakdown": {"D": 0.856, "G": 0.82, "V": 0.68, "F": 0.74, "O": 0.0},
        "evidence": {
            "udise_ref": "UDISE+ U09130101001 — Govt Primary Sigra (Enrollment 612 vs Capacity 440, 8 teachers, building: poor)",
            "census_ref": "ward_07 — Pop: 18,420, Literacy: 71%, Vulnerability index: 0.68, BPL: 31%, SC/ST: 24%",
            "maps_ref": "Nearest facility: Heritage Hospital — 3.8 km, 16 min by road (MOCK)",
            "plan_ref": "No overlapping active scheme found in 2025-26 district plan.",
        },
        "cost_estimate": 12.5,
        "beneficiaries": 612,
        "status": "Under Review",
        "lat": 25.3120,
        "lng": 82.9847,
        "last_updated": "2026-07-01T10:00:00Z",
        "submission_ids": [],
    },
    {
        "id": "cluster_ward04_roads_002",
        "name": "Sigra Marg — Potholes & Monsoon Waterlogging",
        "category": "roads",
        "ward_id": "ward_04",
        "location": "Sigra Marg, Ward 4, Varanasi Cantonment",
        "demand_count": 189,
        "priority_score": 82.0,
        "score_breakdown": {"D": 0.756, "G": 0.75, "V": 0.62, "F": 0.72, "O": 0.5},
        "evidence": {
            "udise_ref": "UDISE+ U09130101001 — Govt Primary Sigra (Enrollment 612 vs Capacity 440)",
            "census_ref": "ward_04 — Pop: 22,150, Literacy: 74%, Vulnerability index: 0.62, BPL: 28%",
            "maps_ref": "Nearest facility: Heritage Hospital — 2.4 km, 11 min by road (MOCK)",
            "plan_ref": "△ Partial overlap: Smart City Road Resurfacing Phase-3 (Status: Tendering) — coordinate before proceeding",
        },
        "cost_estimate": 38.0,
        "beneficiaries": 2200,
        "status": "Received",
        "lat": 25.3200,
        "lng": 82.9780,
        "last_updated": "2026-07-01T10:00:00Z",
        "submission_ids": [],
    },
    {
        "id": "cluster_ward11_drainage_003",
        "name": "Bhelupur Drainage Overflow — Monsoon Flooding",
        "category": "drainage",
        "ward_id": "ward_11",
        "location": "Bhelupur, Ward 11, Varanasi Cantonment",
        "demand_count": 156,
        "priority_score": 79.0,
        "score_breakdown": {"D": 0.624, "G": 0.71, "V": 0.55, "F": 0.80, "O": 0.0},
        "evidence": {
            "udise_ref": "UDISE+ U09130102003 — Govt Composite School Bhelupur (Enrollment 521 vs Capacity 480)",
            "census_ref": "ward_11 — Pop: 19,870, Literacy: 78%, Vulnerability index: 0.55, BPL: 24%",
            "maps_ref": "Nearest facility: District Hospital Varanasi — 4.1 km, 18 min by road (MOCK)",
            "plan_ref": "No overlapping active scheme found in 2025-26 district plan.",
        },
        "cost_estimate": 28.0,
        "beneficiaries": 3500,
        "status": "Approved",
        "lat": 25.2958,
        "lng": 82.9990,
        "last_updated": "2026-07-01T10:00:00Z",
        "submission_ids": [],
    },
    {
        "id": "cluster_ward15_water_004",
        "name": "Cantonment Water Supply — Daily Shortage Nadesar",
        "category": "water",
        "ward_id": "ward_15",
        "location": "Nadesar, Ward 15, Varanasi Cantonment",
        "demand_count": 134,
        "priority_score": 75.0,
        "score_breakdown": {"D": 0.536, "G": 0.68, "V": 0.72, "F": 0.68, "O": 0.5},
        "evidence": {
            "udise_ref": "UDISE+ U09130103005 — Govt Primary School Nadesar (Enrollment 445 vs Capacity 360)",
            "census_ref": "ward_15 — Pop: 16,340, Literacy: 69%, Vulnerability index: 0.72, BPL: 35%",
            "maps_ref": "Nearest facility: Heritage Hospital — 5.2 km, 23 min by road (MOCK)",
            "plan_ref": "⚠ Overlap: Jal Jeevan Mission — Household Tap Connections (Status: Ongoing) — duplication risk HIGH",
        },
        "cost_estimate": 18.0,
        "beneficiaries": 1634,
        "status": "In Progress",
        "lat": 25.3380,
        "lng": 82.9580,
        "last_updated": "2026-07-01T10:00:00Z",
        "submission_ids": [],
    },
    {
        "id": "cluster_ward07_electricity_005",
        "name": "Orderly Bazaar Streetlights — No Lighting After Dark",
        "category": "electricity",
        "ward_id": "ward_07",
        "location": "Orderly Bazaar, Ward 7, Varanasi Cantonment",
        "demand_count": 98,
        "priority_score": 68.0,
        "score_breakdown": {"D": 0.392, "G": 0.60, "V": 0.68, "F": 0.76, "O": 0.0},
        "evidence": {
            "udise_ref": "UDISE+ U09130101002 — Govt Upper Primary School Orderly Bazaar (Enrollment 387 vs Capacity 320)",
            "census_ref": "ward_07 — Pop: 18,420, Literacy: 71%, Vulnerability index: 0.68, BPL: 31%",
            "maps_ref": "Nearest facility: Heritage Hospital — 3.2 km, 14 min by road (MOCK)",
            "plan_ref": "No overlapping active scheme found in 2025-26 district plan.",
        },
        "cost_estimate": 6.5,
        "beneficiaries": 950,
        "status": "Received",
        "lat": 25.3198,
        "lng": 82.9762,
        "last_updated": "2026-07-01T10:00:00Z",
        "submission_ids": [],
    },
    {
        "id": "cluster_ward18_health_006",
        "name": "Paharia Health Centre — Chronic Medicine Shortage",
        "category": "health",
        "ward_id": "ward_18",
        "location": "Paharia, Ward 18, Varanasi Cantonment",
        "demand_count": 87,
        "priority_score": 65.0,
        "score_breakdown": {"D": 0.348, "G": 0.70, "V": 0.76, "F": 0.58, "O": 0.0},
        "evidence": {
            "udise_ref": "UDISE+ U09130104007 — Govt Primary School Paharia (Enrollment 312 vs Capacity 280)",
            "census_ref": "ward_18 — Pop: 14,280, Literacy: 65%, Vulnerability index: 0.76, BPL: 38%",
            "maps_ref": "Nearest facility: BHU Sir Sunderlal Hospital — 7.8 km, 34 min by road (MOCK)",
            "plan_ref": "No overlapping active scheme found in 2025-26 district plan.",
        },
        "cost_estimate": 4.5,
        "beneficiaries": 1428,
        "status": "Under Review",
        "lat": 25.3520,
        "lng": 82.9490,
        "last_updated": "2026-07-01T10:00:00Z",
        "submission_ids": [],
    },
    {
        "id": "cluster_ward22_sanitation_007",
        "name": "Girls School Pandeypur — No Functional Toilets",
        "category": "sanitation",
        "ward_id": "ward_22",
        "location": "Pandeypur, Ward 22, Varanasi Cantonment",
        "demand_count": 76,
        "priority_score": 71.0,
        "score_breakdown": {"D": 0.304, "G": 0.85, "V": 0.71, "F": 0.82, "O": 0.0},
        "evidence": {
            "udise_ref": "UDISE+ U09130105008 — Govt Composite School Pandeypur (Enrollment 536 vs Capacity 420)",
            "census_ref": "ward_22 — Pop: 12,950, Literacy: 62%, Vulnerability index: 0.71, BPL: 36%",
            "maps_ref": "Nearest facility: District Hospital Varanasi — 6.4 km, 28 min by road (MOCK)",
            "plan_ref": "No overlapping active scheme found in 2025-26 district plan.",
        },
        "cost_estimate": 3.8,
        "beneficiaries": 536,
        "status": "Approved",
        "lat": 25.3610,
        "lng": 82.9420,
        "last_updated": "2026-07-01T10:00:00Z",
        "submission_ids": [],
    },
    {
        "id": "cluster_ward04_safety_008",
        "name": "Sigra Footpath Encroachment — Pedestrian Safety Hazard",
        "category": "safety",
        "ward_id": "ward_04",
        "location": "Sigra, Ward 4, Varanasi Cantonment",
        "demand_count": 65,
        "priority_score": 58.0,
        "score_breakdown": {"D": 0.260, "G": 0.55, "V": 0.62, "F": 0.65, "O": 0.0},
        "evidence": {
            "udise_ref": "UDISE+ U09130101001 — Govt Primary Sigra (Enrollment 612 vs Capacity 440)",
            "census_ref": "ward_04 — Pop: 22,150, Literacy: 74%, Vulnerability index: 0.62, BPL: 28%",
            "maps_ref": "Nearest facility: Heritage Hospital — 2.6 km, 12 min by road (MOCK)",
            "plan_ref": "No overlapping active scheme found in 2025-26 district plan.",
        },
        "cost_estimate": 5.0,
        "beneficiaries": 2215,
        "status": "Received",
        "lat": 25.3185,
        "lng": 82.9795,
        "last_updated": "2026-07-01T10:00:00Z",
        "submission_ids": [],
    },
    {
        "id": "cluster_ward11_anganwadi_009",
        "name": "Bhelupur Anganwadi — Structural Damage",
        "category": "anganwadi",
        "ward_id": "ward_11",
        "location": "Bhelupur, Ward 11, Varanasi Cantonment",
        "demand_count": 54,
        "priority_score": 62.0,
        "score_breakdown": {"D": 0.216, "G": 0.72, "V": 0.55, "F": 0.78, "O": 0.0},
        "evidence": {
            "udise_ref": "UDISE+ U09130102003 — Govt Composite School Bhelupur (Enrollment 521 vs Capacity 480)",
            "census_ref": "ward_11 — Pop: 19,870, Literacy: 78%, Vulnerability index: 0.55, BPL: 24%",
            "maps_ref": "Nearest facility: District Hospital Varanasi — 4.1 km, 18 min by road (MOCK)",
            "plan_ref": "No overlapping active scheme found in 2025-26 district plan.",
        },
        "cost_estimate": 7.2,
        "beneficiaries": 320,
        "status": "Under Review",
        "lat": 25.2975,
        "lng": 82.9975,
        "last_updated": "2026-07-01T10:00:00Z",
        "submission_ids": [],
    },
    {
        "id": "cluster_ward15_housing_010",
        "name": "Nadesar Vocational Centre — Proposed Land Site",
        "category": "housing",
        "ward_id": "ward_15",
        "location": "Nadesar, Ward 15, Varanasi Cantonment",
        "demand_count": 42,
        "priority_score": 41.0,
        "score_breakdown": {"D": 0.168, "G": 0.40, "V": 0.72, "F": 0.45, "O": 0.5},
        "evidence": {
            "udise_ref": "UDISE+ U09130103005 — Govt Primary School Nadesar (Enrollment 445 vs Capacity 360)",
            "census_ref": "ward_15 — Pop: 16,340, Literacy: 69%, Vulnerability index: 0.72, BPL: 35%",
            "maps_ref": "Nearest facility: Heritage Hospital — 5.2 km, 23 min by road (MOCK)",
            "plan_ref": "△ Partial overlap: Jal Jeevan Mission related land acquisition (Status: Tendering)",
        },
        "cost_estimate": 55.0,
        "beneficiaries": 800,
        "status": "Received",
        "lat": 25.3370,
        "lng": 82.9600,
        "last_updated": "2026-07-01T10:00:00Z",
        "submission_ids": [],
    },
    {
        "id": "cluster_ward18_parks_011",
        "name": "Shivpur Park — Overgrown & Unsafe",
        "category": "parks",
        "ward_id": "ward_18",
        "location": "Shivpur, Ward 18, Varanasi Cantonment",
        "demand_count": 38,
        "priority_score": 35.0,
        "score_breakdown": {"D": 0.152, "G": 0.30, "V": 0.76, "F": 0.55, "O": 0.0},
        "evidence": {
            "udise_ref": "UDISE+ U09130104007 — Govt Primary School Paharia (Enrollment 312 vs Capacity 280)",
            "census_ref": "ward_18 — Pop: 14,280, Literacy: 65%, Vulnerability index: 0.76, BPL: 38%",
            "maps_ref": "Nearest facility: BHU Sir Sunderlal Hospital — 7.2 km, 31 min by road (MOCK)",
            "plan_ref": "No overlapping active scheme found in 2025-26 district plan.",
        },
        "cost_estimate": 4.0,
        "beneficiaries": 1428,
        "status": "Received",
        "lat": 25.3498,
        "lng": 82.9508,
        "last_updated": "2026-07-01T10:00:00Z",
        "submission_ids": [],
    },
    {
        "id": "cluster_ward22_housing_012",
        "name": "Pandeypur Community Hall — Leaking Roof Repair",
        "category": "housing",
        "ward_id": "ward_22",
        "location": "Pandeypur, Ward 22, Varanasi Cantonment",
        "demand_count": 31,
        "priority_score": 44.0,
        "score_breakdown": {"D": 0.124, "G": 0.48, "V": 0.71, "F": 0.72, "O": 0.0},
        "evidence": {
            "udise_ref": "UDISE+ U09130105008 — Govt Composite School Pandeypur (Enrollment 536 vs Capacity 420)",
            "census_ref": "ward_22 — Pop: 12,950, Literacy: 62%, Vulnerability index: 0.71, BPL: 36%",
            "maps_ref": "Nearest facility: District Hospital Varanasi — 6.4 km, 28 min by road (MOCK)",
            "plan_ref": "No overlapping active scheme found in 2025-26 district plan.",
        },
        "cost_estimate": 3.2,
        "beneficiaries": 500,
        "status": "Received",
        "lat": 25.3625,
        "lng": 82.9435,
        "last_updated": "2026-07-01T10:00:00Z",
        "submission_ids": [],
    },
]


async def seed_canonical_clusters() -> int:
    """Seed the 12 pre-computed canonical clusters."""
    count = 0
    for cluster in CANONICAL_CLUSTERS:
        await save_cluster(cluster)
        await save_cluster_realtime(cluster)
        count += 1
    return count


async def seed_submissions() -> tuple[int, int]:
    """
    Load synthetic_submissions.json, run each through the pipeline,
    and return (submissions_seeded, clusters_created).
    """
    sub_file = _DATA_DIR / "synthetic_submissions.json"
    if not sub_file.exists():
        print(f"⚠  {sub_file} not found — skipping submission seeding.")
        return 0, 0

    raw_list: list[dict] = json.loads(sub_file.read_text(encoding="utf-8"))

    seeded_count = 0
    from utils.bigquery_client import get_in_memory_clusters

    for raw in raw_list:
        try:
            sub_create = SubmissionCreate(**raw)
            enriched = await process_submission(sub_create)

            # Dedup
            all_clusters = list(get_in_memory_clusters().values())
            cluster_id = await find_or_create_cluster(enriched, all_clusters)
            enriched["cluster_id"] = cluster_id
            enriched["processed"] = True

            # Save submission
            await save_submission(enriched)
            await save_submission_realtime(enriched)

            # Update cluster scores
            cluster = get_in_memory_clusters().get(cluster_id)
            if cluster:
                evidence = await fetch_evidence(cluster)
                scoring = compute_priority_score(cluster, evidence)
                cluster["priority_score"] = scoring["priority_score"]
                cluster["score_breakdown"] = scoring["score_breakdown"]
                cluster["cost_estimate"] = scoring["cost_estimate"]
                cluster["beneficiaries"] = scoring["beneficiaries"]
                cluster["evidence"] = {
                    "udise_ref": evidence.get("udise_ref"),
                    "census_ref": evidence.get("census_ref"),
                    "maps_ref": evidence.get("maps_ref"),
                    "plan_ref": evidence.get("plan_ref"),
                }
                await save_cluster(cluster)

            seeded_count += 1
            if seeded_count % 50 == 0:
                print(f"  … processed {seeded_count} submissions")
        except Exception as exc:
            print(f"  ⚠  Error processing submission: {exc}")

    cluster_count = len(get_in_memory_clusters())
    return seeded_count, cluster_count


async def main():
    print("=" * 60)
    print("  JanSetu Data Seeding Script")
    print("=" * 60)

    init_bigquery()
    init_firestore()

    print("\n[1/2] Seeding 12 canonical clusters …")
    cluster_count = await seed_canonical_clusters()
    print(f"  ✅  {cluster_count} canonical clusters seeded.")

    print("\n[2/2] Processing synthetic submissions …")
    sub_count, dynamic_clusters = await seed_submissions()
    print(f"  ✅  {sub_count} submissions seeded → {dynamic_clusters} total clusters.")

    print("\n" + "=" * 60)
    print(f"  DONE: {sub_count} submissions → {dynamic_clusters} clusters")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
