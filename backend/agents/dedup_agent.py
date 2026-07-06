"""
Dedup & Clustering Agent.

Responsibilities:
  1. Compute semantic embedding for a new submission
  2. Compare against centroids of existing clusters (same category + ward)
  3. Merge into an existing cluster if cosine similarity > 0.82
  4. Otherwise create a new cluster seeded by this submission
  5. Maintain per-cluster centroid by averaging member embeddings
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from utils.vertex_embeddings import compute_centroid, cosine_similarity, get_embedding

logger = logging.getLogger(__name__)

# ── Tuneable thresholds ────────────────────────────────────────────────────────
SIMILARITY_THRESHOLD = 0.82   # cosine similarity above which we merge
MAX_CLUSTER_SIZE = 500        # safety cap — prevent runaway mega-clusters


async def find_or_create_cluster(
    submission: dict,
    existing_clusters: list[dict],
) -> str:
    """
    Find the best matching cluster for *submission* or create a new one.

    Algorithm:
      1. Embed the submission text.
      2. Filter existing clusters by same category AND same ward_id.
      3. For each candidate, compute cosine similarity vs its stored centroid.
      4. If best similarity > SIMILARITY_THRESHOLD and cluster size < MAX_CLUSTER_SIZE
         → merge: increment demand_count, add submission_id, recompute centroid.
      5. Else → create a new cluster from this submission.

    Side-effects:
      • Mutates the matched cluster dict in-place (demand_count, submission_ids, centroid).
      • Adds a new cluster dict to existing_clusters if a new one is created.

    Returns the cluster_id (str).
    """
    text = submission.get("text") or submission.get("description") or ""
    embedding = await get_embedding(text)

    category = submission.get("category", "other")
    ward_id = submission.get("ward_id", "ward_unknown")

    # ── Filter candidates ──────────────────────────────────────────────────────
    candidates = [
        c for c in existing_clusters
        if c.get("category") == category
        and c.get("ward_id") == ward_id
        and c.get("demand_count", 0) < MAX_CLUSTER_SIZE
    ]

    best_cluster: dict | None = None
    best_similarity: float = -1.0

    for cluster in candidates:
        centroid = cluster.get("centroid")
        if not centroid:
            continue
        sim = cosine_similarity(embedding, centroid)
        if sim > best_similarity:
            best_similarity = sim
            best_cluster = cluster

    # ── Decision ───────────────────────────────────────────────────────────────
    if best_cluster is not None and best_similarity >= SIMILARITY_THRESHOLD:
        cluster_id = _merge_into_cluster(best_cluster, submission, embedding)
        logger.info(
            "Merged submission %s → cluster %s (similarity=%.3f)",
            submission.get("id"),
            cluster_id,
            best_similarity,
        )
    else:
        cluster_id = _create_cluster(submission, embedding, existing_clusters)
        logger.info(
            "Created new cluster %s for submission %s (best_sim=%.3f)",
            cluster_id,
            submission.get("id"),
            best_similarity,
        )

    return cluster_id


# ── Private helpers ────────────────────────────────────────────────────────────

def _merge_into_cluster(
    cluster: dict,
    submission: dict,
    embedding: list[float],
) -> str:
    """Merge a submission into an existing cluster, updating centroid."""
    cluster["demand_count"] = cluster.get("demand_count", 1) + 1

    sub_ids: list[str] = cluster.get("submission_ids", [])
    sub_id = submission.get("id")
    if sub_id and sub_id not in sub_ids:
        sub_ids.append(sub_id)
    cluster["submission_ids"] = sub_ids

    # Update running centroid (incremental average)
    stored_embeddings: list[list[float]] = cluster.get("member_embeddings", [])
    stored_embeddings.append(embedding)
    # Keep last 100 to bound memory usage
    if len(stored_embeddings) > 100:
        stored_embeddings = stored_embeddings[-100:]
    cluster["member_embeddings"] = stored_embeddings
    cluster["centroid"] = compute_centroid(stored_embeddings)

    cluster["last_updated"] = datetime.now(timezone.utc).isoformat()
    return cluster["id"]


def _create_cluster(
    submission: dict,
    embedding: list[float],
    existing_clusters: list[dict],
) -> str:
    """Initialise a new cluster from a seed submission and append to existing_clusters."""
    cluster_id = f"cluster_{submission.get('ward_id', 'unk')}_{submission.get('category', 'other')}_{uuid.uuid4().hex[:8]}"

    lat = submission.get("lat") or 12.9716   # Default: Bangalore South centre
    lng = submission.get("lng") or 77.594670

    name = _generate_cluster_name(submission)

    new_cluster: dict[str, Any] = {
        "id": cluster_id,
        "name": name,
        "category": submission.get("category", "other"),
        "ward_id": submission.get("ward_id", "ward_unknown"),
        "location": submission.get("location", "Varanasi Cantonment"),
        "demand_count": 1,
        "priority_score": 0.0,          # Will be set by scoring_agent
        "score_breakdown": {"D": 0.0, "G": 0.0, "V": 0.0, "F": 0.0, "O": 0.0},
        "evidence": {
            "udise_ref": None,
            "census_ref": None,
            "maps_ref": None,
            "plan_ref": None,
        },
        "cost_estimate": 0.0,
        "beneficiaries": 0,
        "status": "Received",
        "lat": lat,
        "lng": lng,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "submission_ids": [submission.get("id")] if submission.get("id") else [],
        "centroid": embedding,
        "member_embeddings": [embedding],
    }

    existing_clusters.append(new_cluster)
    return cluster_id


def _generate_cluster_name(submission: dict) -> str:
    """Generate a human-readable cluster name from submission fields."""
    category = submission.get("category", "other").title()
    location = submission.get("location", "Varanasi Cantonment")
    # Truncate location if too long
    if len(location) > 40:
        location = location[:40].rsplit(" ", 1)[0]
    return f"{location} — {category} Issue"
