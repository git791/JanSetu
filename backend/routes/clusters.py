"""
/api/clusters endpoints — retrieve and manage need-clusters.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from agents.notification_agent import notify_cluster_status_change
from agents.scoring_agent import compute_priority_score
from agents.evidence_agent import fetch_evidence
from utils.bigquery_client import (
    get_cluster_by_id,
    get_clusters,
    save_cluster,
    update_cluster_field,
)
from utils.firestore_client import update_cluster_status, save_cluster_realtime

logger = logging.getLogger(__name__)
router = APIRouter(tags=["clusters"])

_VALID_STATUSES = {"Received", "Under Review", "Approved", "In Progress", "Completed"}


# ── GET /api/clusters ─────────────────────────────────────────────────────────

@router.get("/api/clusters")
async def list_clusters(
    ward_id: str | None = None,
    category: str | None = None,
    status: str | None = None,
    limit: int = 50,
):
    """
    Return all need-clusters sorted by priority_score descending.

    Optional query filters: ward_id, category, status.
    """
    try:
        clusters = await get_clusters()

        if ward_id:
            clusters = [c for c in clusters if c.get("ward_id") == ward_id]
        if category:
            clusters = [c for c in clusters if c.get("category") == category]
        if status:
            clusters = [c for c in clusters if c.get("status") == status]

        # Remove internal-only fields before returning
        for c in clusters:
            c.pop("centroid", None)
            c.pop("member_embeddings", None)

        return {"clusters": clusters[:limit], "total": len(clusters)}
    except Exception as exc:
        logger.exception("Error in GET /api/clusters")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── GET /api/clusters/{cluster_id} ────────────────────────────────────────────

@router.get("/api/clusters/{cluster_id}")
async def get_cluster(cluster_id: str):
    """
    Return a single cluster with full citation_cards for the explainability panel.
    """
    try:
        cluster = await get_cluster_by_id(cluster_id)
        if not cluster:
            raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found.")

        # Recompute citation cards on-the-fly (keeps them fresh)
        try:
            evidence = await fetch_evidence(cluster)
            scoring = compute_priority_score(cluster, evidence)
            cluster["citation_cards"] = scoring["citation_cards"]
        except Exception as exc:
            logger.warning("Could not recompute citation_cards for %s: %s", cluster_id, exc)
            cluster.setdefault("citation_cards", [])

        # Strip internal fields
        cluster.pop("centroid", None)
        cluster.pop("member_embeddings", None)

        return cluster
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error in GET /api/clusters/%s", cluster_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── PATCH /api/clusters/{cluster_id}/status ──────────────────────────────────

class StatusUpdate(BaseModel):
    status: str
    citizen_phones: list[str] = []


@router.patch("/api/clusters/{cluster_id}/status")
async def update_status(cluster_id: str, body: StatusUpdate):
    """
    Update the status of a need-cluster and send notifications to citizens.
    """
    if body.status not in _VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{body.status}'. Must be one of: {sorted(_VALID_STATUSES)}",
        )

    cluster = await get_cluster_by_id(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster '{cluster_id}' not found.")

    old_status = cluster.get("status", "Received")
    new_status = body.status

    # Persist status update
    cluster["status"] = new_status
    cluster["last_updated"] = datetime.now(timezone.utc).isoformat()

    await update_cluster_field(cluster_id, "status", new_status)
    await update_cluster_status(cluster_id, new_status)
    await save_cluster(cluster)

    # Notify citizens
    notif_result = await notify_cluster_status_change(
        cluster_id, new_status, body.citizen_phones
    )

    logger.info(
        "Cluster %s status: %s → %s | notif=%s",
        cluster_id,
        old_status,
        new_status,
        notif_result,
    )

    return {
        "cluster_id": cluster_id,
        "old_status": old_status,
        "new_status": new_status,
        "notification": notif_result,
    }
