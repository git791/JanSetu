"""
Explainable Priority Scoring Agent.

Computes a 0-100 priority score for a need-cluster using the formula:

    Priority Score = 100 × (w1·D + w2·G + w3·V + w4·F − w5·O)

Where (default weights):
    D  — Demand Intensity      w1 = 0.30
    G  — Need Gap              w2 = 0.25
    V  — Vulnerability Index   w3 = 0.20
    F  — Feasibility           w4 = 0.15
    O  — Overlap Penalty       w5 = 0.10

Each component is normalised to [0, 1].  The raw score is clamped to [0, 100].
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Default weights ────────────────────────────────────────────────────────────
DEFAULT_WEIGHTS: dict[str, float] = {
    "w1": 0.30,  # Demand Intensity
    "w2": 0.25,  # Need Gap
    "w3": 0.20,  # Vulnerability
    "w4": 0.15,  # Feasibility
    "w5": 0.10,  # Overlap Penalty
}

# ── Benchmarks for normalisation ──────────────────────────────────────────────
MAX_DEMAND_IN_CONSTITUENCY = 250    # submissions — tune per constituency
BENCHMARK_COST_PER_BENEFICIARY = 2.0   # ₹ thousands per beneficiary (typical)
MAX_TRAVEL_MINUTES = 60.0           # beyond 60 min → F = 1.0 (urgent)


def compute_priority_score(
    cluster: dict,
    evidence: dict,
    weights: dict | None = None,
) -> dict:
    """
    Compute a priority score for *cluster* using fused *evidence*.

    Args:
        cluster: Cluster dict (must have demand_count, cost_estimate, beneficiaries).
        evidence: Evidence dict from evidence_agent.fetch_evidence().
        weights: Optional override of DEFAULT_WEIGHTS.

    Returns a dict:
        {
            priority_score: float,          # 0-100
            score_breakdown: {D, G, V, F, O},
            cost_estimate: float,           # lakhs INR
            beneficiaries: int,
            citation_cards: list[dict],     # one card per factor
        }
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}

    # ── D — Demand Intensity ──────────────────────────────────────────────────
    demand_count = max(cluster.get("demand_count", 1), 1)
    D = min(demand_count / MAX_DEMAND_IN_CONSTITUENCY, 1.0)

    # ── G — Need Gap ─────────────────────────────────────────────────────────
    G = float(evidence.get("need_gap_value", 0.5))
    G = max(0.0, min(G, 1.0))

    # ── V — Vulnerability Index ───────────────────────────────────────────────
    V = float(evidence.get("vulnerability_index", 0.5))
    V = max(0.0, min(V, 1.0))

    # ── F — Feasibility ───────────────────────────────────────────────────────
    # Derived from travel time: longer travel → higher F (harder to access, more urgent)
    # and cost-per-beneficiary vs benchmark
    travel_min = float(evidence.get("travel_minutes", 30.0))
    F_access = min(travel_min / MAX_TRAVEL_MINUTES, 1.0)

    beneficiaries = max(cluster.get("beneficiaries", 1), 1)
    cost_estimate_lakhs = cluster.get("cost_estimate", 0.0) or 0.0
    # Convert lakhs to thousands: 1 lakh = 100 thousands
    cost_thousands = cost_estimate_lakhs * 100.0
    cost_per_ben = cost_thousands / beneficiaries if beneficiaries > 0 else BENCHMARK_COST_PER_BENEFICIARY

    # Lower cost-per-beneficiary → higher feasibility (value for money)
    if cost_per_ben <= 0:
        F_cost = 0.5
    else:
        ratio = BENCHMARK_COST_PER_BENEFICIARY / cost_per_ben
        F_cost = min(ratio, 1.0)

    F = round((F_access + F_cost) / 2.0, 4)

    # ── O — Overlap Penalty ───────────────────────────────────────────────────
    O = float(evidence.get("plan_overlap", 0.0))
    O = max(0.0, min(O, 1.0))

    # ── Raw score ─────────────────────────────────────────────────────────────
    raw = w["w1"] * D + w["w2"] * G + w["w3"] * V + w["w4"] * F - w["w5"] * O
    priority_score = round(max(0.0, min(raw * 100.0, 100.0)), 2)

    score_breakdown = {
        "D": round(D, 4),
        "G": round(G, 4),
        "V": round(V, 4),
        "F": round(F, 4),
        "O": round(O, 4),
    }

    # ── Cost / beneficiary estimates ──────────────────────────────────────────
    # If cost_estimate not yet set, derive a rough estimate from category
    if cost_estimate_lakhs <= 0:
        cost_estimate_lakhs = _estimate_cost(cluster.get("category", "other"), demand_count)

    if beneficiaries <= 1:
        beneficiaries = _estimate_beneficiaries(cluster.get("category", "other"), demand_count)

    # ── Citation cards (explainability) ───────────────────────────────────────
    citation_cards = _build_citation_cards(
        D=D, G=G, V=V, F=F, O=O,
        cluster=cluster,
        evidence=evidence,
        weights=w,
    )

    return {
        "priority_score": priority_score,
        "score_breakdown": score_breakdown,
        "cost_estimate": round(cost_estimate_lakhs, 2),
        "beneficiaries": beneficiaries,
        "citation_cards": citation_cards,
    }


# ── Private helpers ────────────────────────────────────────────────────────────

_CATEGORY_COST_LAKHS: dict[str, float] = {
    "roads": 35.0,
    "water": 18.0,
    "health": 22.0,
    "education": 12.0,
    "sanitation": 8.0,
    "electricity": 6.0,
    "drainage": 25.0,
    "housing": 50.0,
    "parks": 5.0,
    "safety": 4.0,
    "anganwadi": 7.0,
    "other": 10.0,
}

_CATEGORY_BEN_PER_DEMAND: dict[str, int] = {
    "roads": 800,
    "water": 600,
    "health": 500,
    "education": 200,
    "sanitation": 400,
    "electricity": 350,
    "drainage": 700,
    "housing": 300,
    "parks": 250,
    "safety": 450,
    "anganwadi": 150,
    "other": 200,
}


def _estimate_cost(category: str, demand_count: int) -> float:
    """Rough cost estimate in lakhs INR based on category."""
    base = _CATEGORY_COST_LAKHS.get(category, 10.0)
    # Scale slightly with demand (more citizens = larger project)
    scale = 1.0 + (demand_count / 500.0) * 0.5
    return round(base * scale, 2)


def _estimate_beneficiaries(category: str, demand_count: int) -> int:
    """Rough beneficiary estimate based on category and demand count."""
    per_demand = _CATEGORY_BEN_PER_DEMAND.get(category, 200)
    return max(demand_count * 3, per_demand)


def _build_citation_cards(
    D: float, G: float, V: float, F: float, O: float,
    cluster: dict,
    evidence: dict,
    weights: dict,
) -> list[dict]:
    """Build human-readable citation cards for the dashboard explainability panel."""
    demand_count = cluster.get("demand_count", 1)
    category = cluster.get("category", "other").title()

    cards = [
        {
            "factor": "D",
            "label": "Demand Intensity",
            "weight": weights["w1"],
            "value": round(D, 3),
            "weighted_contribution": round(weights["w1"] * D * 100, 2),
            "source": f"{demand_count} citizen submissions in this cluster",
            "narrative": (
                f"{demand_count} residents have reported this {category} issue. "
                f"This represents {int(D*100)}% of the constituency's peak demand threshold."
            ),
        },
        {
            "factor": "G",
            "label": "Need Gap",
            "weight": weights["w2"],
            "value": round(G, 3),
            "weighted_contribution": round(weights["w2"] * G * 100, 2),
            "source": evidence.get("udise_ref") or "Local facility data",
            "narrative": (
                f"The local infrastructure gap score is {int(G*100)}%. "
                + (
                    "High overcrowding or poor building condition detected."
                    if G > 0.6
                    else "Moderate service gap identified."
                )
            ),
        },
        {
            "factor": "V",
            "label": "Vulnerability Index",
            "weight": weights["w3"],
            "value": round(V, 3),
            "weighted_contribution": round(weights["w3"] * V * 100, 2),
            "source": evidence.get("census_ref") or "Census 2021",
            "narrative": (
                f"Ward vulnerability index: {int(V*100)}%. "
                + (
                    "High concentration of BPL households and SC/ST population."
                    if V > 0.55
                    else "Moderate socio-economic vulnerability."
                )
            ),
        },
        {
            "factor": "F",
            "label": "Feasibility & Access",
            "weight": weights["w4"],
            "value": round(F, 3),
            "weighted_contribution": round(weights["w4"] * F * 100, 2),
            "source": evidence.get("maps_ref") or "Distance estimate",
            "narrative": (
                f"Feasibility score {int(F*100)}%. "
                + evidence.get("maps_ref", "Travel time to nearest facility.")
            ),
        },
        {
            "factor": "O",
            "label": "Overlap Penalty",
            "weight": weights["w5"],
            "value": round(O, 3),
            "weighted_contribution": round(-weights["w5"] * O * 100, 2),
            "source": evidence.get("plan_ref") or "District development plan",
            "narrative": (
                evidence.get("plan_ref")
                or "No active scheme overlap found."
            ),
        },
    ]
    return cards
