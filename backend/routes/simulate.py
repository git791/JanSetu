"""
/api/simulate endpoint — budget simulation for the MLA dashboard.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from utils.bigquery_client import get_cluster_by_id, get_clusters

logger = logging.getLogger(__name__)
router = APIRouter(tags=["simulate"])


class SimulateRequest(BaseModel):
    cluster_ids: list[str] = Field(..., description="IDs of clusters to include in the simulation")
    budget: float = Field(..., gt=0, description="Available budget in lakhs INR")

    model_config = {"json_schema_extra": {
        "example": {
            "cluster_ids": ["cluster_ward07_edu_001", "cluster_ward04_roads_002"],
            "budget": 100.0,
        }
    }}


@router.post("/api/simulate")
async def simulate(data: SimulateRequest):
    """
    Run a budget simulation across the selected clusters.

    Returns:
      - total_cost: sum of cost_estimate for selected clusters (lakhs INR)
      - total_beneficiaries: sum of beneficiaries
      - impact_score: priority-weighted average beneficiary impact (0-100)
      - over_budget: bool
      - roi: beneficiaries per lakh INR
      - clusters: list of selected cluster summaries with status
    """
    if not data.cluster_ids:
        raise HTTPException(status_code=400, detail="cluster_ids cannot be empty.")

    if len(data.cluster_ids) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 clusters per simulation.")

    try:
        # ── Fetch clusters ─────────────────────────────────────────────────────
        selected: list[dict] = []
        missing: list[str] = []

        for cid in data.cluster_ids:
            cluster = await get_cluster_by_id(cid)
            if cluster:
                selected.append(cluster)
            else:
                missing.append(cid)

        if not selected:
            raise HTTPException(status_code=404, detail="None of the provided cluster_ids were found.")

        # ── Aggregations ───────────────────────────────────────────────────────
        total_cost = sum(c.get("cost_estimate", 0.0) for c in selected)
        total_beneficiaries = sum(c.get("beneficiaries", 0) for c in selected)
        over_budget = total_cost > data.budget
        remaining_budget = round(data.budget - total_cost, 2)

        # ── Impact score: priority-score-weighted beneficiary fraction ─────────
        if total_beneficiaries > 0:
            weighted_sum = sum(
                c.get("priority_score", 0.0) * c.get("beneficiaries", 0)
                for c in selected
            )
            impact_score = round(weighted_sum / total_beneficiaries, 2)
        else:
            impact_score = 0.0

        # ROI: citizens served per lakh INR
        roi = round(total_beneficiaries / total_cost, 1) if total_cost > 0 else 0.0

        # ── Build cluster summaries ────────────────────────────────────────────
        cluster_summaries = [
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "category": c.get("category"),
                "ward_id": c.get("ward_id"),
                "priority_score": c.get("priority_score", 0.0),
                "cost_estimate": c.get("cost_estimate", 0.0),
                "beneficiaries": c.get("beneficiaries", 0),
                "status": c.get("status"),
                "demand_count": c.get("demand_count", 0),
            }
            for c in selected
        ]

        # Sort by priority_score desc within the selection
        cluster_summaries.sort(key=lambda x: x["priority_score"], reverse=True)

        # ── Build recommendations ──────────────────────────────────────────────
        recommendations = _build_recommendations(selected, data.budget, total_cost, over_budget)

        return {
            "total_cost": round(total_cost, 2),
            "total_beneficiaries": total_beneficiaries,
            "impact_score": impact_score,
            "over_budget": over_budget,
            "budget_available": data.budget,
            "remaining_budget": remaining_budget,
            "roi": roi,
            "clusters_included": len(selected),
            "clusters_missing": missing,
            "clusters": cluster_summaries,
            "recommendations": recommendations,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in POST /api/simulate")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _build_recommendations(
    clusters: list[dict],
    budget: float,
    total_cost: float,
    over_budget: bool,
) -> list[str]:
    """Generate plain-language recommendations for the MLA."""
    recs: list[str] = []

    if over_budget:
        shortage = total_cost - budget
        recs.append(
            f"⚠️  Total cost ₹{total_cost:.1f}L exceeds budget by ₹{shortage:.1f}L. "
            "Consider phasing — implement top-priority clusters in Year 1."
        )
        # Suggest which to drop
        by_score = sorted(clusters, key=lambda c: c.get("priority_score", 0))
        if by_score:
            worst = by_score[0]
            recs.append(
                f"💡  Lowest-priority cluster '{worst.get('name')}' (score {worst.get('priority_score', 0):.0f}) "
                "could be deferred to save ₹"
                f"{worst.get('cost_estimate', 0):.1f}L."
            )
    else:
        remaining = budget - total_cost
        recs.append(
            f"✅  All {len(clusters)} clusters fit within budget with ₹{remaining:.1f}L remaining."
        )
        if remaining > 5:
            recs.append(
                f"💡  Remaining ₹{remaining:.1f}L could fund smaller maintenance items "
                "or be reserved for emergency response."
            )

    high_vuln = [c for c in clusters if c.get("score_breakdown", {}).get("V", 0) > 0.6]
    if high_vuln:
        recs.append(
            f"🎯  {len(high_vuln)} cluster(s) serve high-vulnerability wards (VI > 0.6) — "
            "prioritise these for maximum social equity impact."
        )

    return recs
