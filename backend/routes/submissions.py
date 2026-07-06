"""
/api/submit endpoint — citizen submission intake.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from agents.dedup_agent import find_or_create_cluster
from agents.evidence_agent import fetch_evidence
from agents.intake_agent import process_submission
from agents.scoring_agent import compute_priority_score
from schemas.submission import SubmissionCreate
from utils.bigquery_client import (
    get_in_memory_clusters,
    save_cluster,
    save_submission,
    get_submission,
)
from utils.firestore_client import save_submission_realtime, save_cluster_realtime

logger = logging.getLogger(__name__)
router = APIRouter(tags=["submissions"])


# ── POST /api/submit ──────────────────────────────────────────────────────────

@router.post("/api/submit", status_code=status.HTTP_202_ACCEPTED)
async def submit(data: SubmissionCreate, background_tasks: BackgroundTasks):
    """
    Accept a citizen submission, run intake normalisation synchronously,
    then kick off the dedup → evidence → scoring pipeline in the background.

    Returns immediately with a tracking ID so the frontend isn't blocked.
    """
    try:
        # ── Synchronous intake ────────────────────────────────────────────────
        enriched = await process_submission(data)
        submission_id = enriched["id"]

        # ── Persist (dual write: Firestore for real-time, BigQuery for analytics)
        await save_submission(enriched)
        await save_submission_realtime(enriched)

        # ── Background pipeline ───────────────────────────────────────────────
        background_tasks.add_task(_run_pipeline, submission_id)

        return {
            "id": submission_id,
            "tracking_id": submission_id[-8:].upper(),
            "message": (
                "Submission received. Your issue is being processed. "
                f"Track using ID: {submission_id[-8:].upper()}"
            ),
            "ward_id": enriched.get("ward_id"),
            "category": enriched.get("category"),
            "authenticity_score": enriched.get("authenticity_score"),
        }
    except Exception as exc:
        logger.exception("Error in /api/submit")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Background pipeline ────────────────────────────────────────────────────────

async def _run_pipeline(submission_id: str) -> None:
    """
    Full processing pipeline for a submission (runs in background):
      1. Dedup / cluster assignment
      2. Evidence fusion
      3. Priority scoring
      4. Persist updated cluster
    """
    try:
        from utils.bigquery_client import get_in_memory_submissions

        submissions = get_in_memory_submissions()
        submission = submissions.get(submission_id)
        if not submission:
            logger.error("Pipeline: submission %s not found in store.", submission_id)
            return

        # ── 1. Dedup → cluster assignment ─────────────────────────────────────
        clusters_store = get_in_memory_clusters()
        all_clusters = list(clusters_store.values())

        cluster_id = await find_or_create_cluster(submission, all_clusters)
        submission["cluster_id"] = cluster_id
        submission["processed"] = True

        # Fetch the updated cluster (it was mutated in-place by dedup_agent)
        cluster = clusters_store.get(cluster_id)
        if not cluster:
            # Dedup agent appends new clusters to the all_clusters list
            for c in all_clusters:
                if c["id"] == cluster_id:
                    cluster = c
                    clusters_store[cluster_id] = cluster
                    break
                    
        if not cluster:
            logger.error("Pipeline: cluster %s not found after dedup.", cluster_id)
            return

        # ── 2. Evidence fusion ────────────────────────────────────────────────
        evidence = await fetch_evidence(cluster)

        # ── 3. Priority scoring ────────────────────────────────────────────────
        scoring_result = compute_priority_score(cluster, evidence)

        # ── 4. Update cluster with new scores ─────────────────────────────────
        cluster["priority_score"] = scoring_result["priority_score"]
        cluster["score_breakdown"] = scoring_result["score_breakdown"]
        cluster["cost_estimate"] = scoring_result["cost_estimate"]
        cluster["beneficiaries"] = scoring_result["beneficiaries"]
        cluster["evidence"] = {
            "udise_ref": evidence.get("udise_ref"),
            "census_ref": evidence.get("census_ref"),
            "maps_ref": evidence.get("maps_ref"),
            "plan_ref": evidence.get("plan_ref"),
        }

        # ── 5. Persist ────────────────────────────────────────────────────────
        await save_cluster(cluster)
        await save_cluster_realtime(cluster)
        await save_submission(submission)

        logger.info(
            "Pipeline complete: submission=%s → cluster=%s score=%.1f",
            submission_id,
            cluster_id,
            scoring_result["priority_score"],
        )
    except Exception as exc:
        logger.exception("Background pipeline error for submission %s: %s", submission_id, exc)
