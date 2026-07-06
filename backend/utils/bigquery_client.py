"""
Google BigQuery client wrapper.

Provides async-compatible helpers for saving and retrieving submissions and
need-clusters.  Falls back to in-memory dicts when BigQuery is not configured,
allowing full local development without GCP credentials.

BigQuery Table DDL
------------------

CREATE TABLE IF NOT EXISTS `{project}.jansetu_mvp.submissions` (
    id            STRING NOT NULL,
    timestamp     TIMESTAMP,
    channel       STRING,
    text          STRING,
    category      STRING,
    location      STRING,
    lang          STRING,
    media_url     STRING,
    lat           FLOAT64,
    lng           FLOAT64,
    phone_hash    STRING,
    ward_id       STRING,
    authenticity_score FLOAT64,
    processed     BOOL,
    cluster_id    STRING
);

CREATE TABLE IF NOT EXISTS `{project}.jansetu_mvp.need_clusters` (
    id              STRING NOT NULL,
    name            STRING,
    category        STRING,
    ward_id         STRING,
    location        STRING,
    demand_count    INT64,
    priority_score  FLOAT64,
    score_D         FLOAT64,
    score_G         FLOAT64,
    score_V         FLOAT64,
    score_F         FLOAT64,
    score_O         FLOAT64,
    evidence_udise  STRING,
    evidence_census STRING,
    evidence_maps   STRING,
    evidence_plan   STRING,
    cost_estimate   FLOAT64,
    beneficiaries   INT64,
    status          STRING,
    lat             FLOAT64,
    lng             FLOAT64,
    last_updated    TIMESTAMP,
    submission_ids  JSON,
    centroid_json   JSON
);
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ── In-memory fallback stores ──────────────────────────────────────────────────
_submissions_store: dict[str, dict] = {}
_clusters_store: dict[str, dict] = {}

# ── BigQuery client ────────────────────────────────────────────────────────────
_bq_client = None
_DATASET = os.getenv("BIGQUERY_DATASET", "jansetu_mvp")
_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
_BQ_AVAILABLE = False


def init_bigquery() -> None:
    """Attempt to initialise the BigQuery client.  Silently falls back on failure."""
    global _bq_client, _BQ_AVAILABLE

    if not _PROJECT:
        logger.warning("GOOGLE_CLOUD_PROJECT not set — BigQuery using in-memory fallback.")
        return

    try:
        from google.cloud import bigquery  # type: ignore

        _bq_client = bigquery.Client(project=_PROJECT)
        _BQ_AVAILABLE = True
        logger.info("BigQuery client initialised (project=%s, dataset=%s).", _PROJECT, _DATASET)
    except Exception as exc:
        logger.warning("Failed to init BigQuery: %s — using in-memory fallback.", exc)


# ── Submissions ────────────────────────────────────────────────────────────────

async def save_submission(submission: dict) -> None:
    """Insert a submission record into BigQuery (or in-memory store)."""
    _submissions_store[submission["id"]] = submission

    if not _BQ_AVAILABLE or _bq_client is None:
        return

    try:
        table_ref = f"{_PROJECT}.{_DATASET}.submissions"
        row = _flatten_submission(submission)
        errors = _bq_client.insert_rows_json(table_ref, [row])
        if errors:
            logger.error("BigQuery insert_rows_json errors: %s", errors)
    except Exception as exc:
        logger.error("save_submission BigQuery error: %s", exc)


async def get_submission(submission_id: str) -> dict | None:
    """Retrieve a single submission by ID."""
    if submission_id in _submissions_store:
        return _submissions_store[submission_id]

    if not _BQ_AVAILABLE or _bq_client is None:
        return None

    try:
        query = (
            f"SELECT * FROM `{_PROJECT}.{_DATASET}.submissions` "
            f"WHERE id = @sub_id LIMIT 1"
        )
        job_config = _bq_client.__class__.__module__  # just to import safely
        from google.cloud import bigquery  # type: ignore

        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("sub_id", "STRING", submission_id)]
        )
        rows = list(_bq_client.query(query, job_config=job_config).result())
        return dict(rows[0]) if rows else None
    except Exception as exc:
        logger.error("get_submission BigQuery error: %s", exc)
        return None


# ── Clusters ───────────────────────────────────────────────────────────────────

async def save_cluster(cluster: dict) -> None:
    """Upsert a need-cluster record (in-memory + BigQuery)."""
    _clusters_store[cluster["id"]] = cluster

    if not _BQ_AVAILABLE or _bq_client is None:
        return

    try:
        # BigQuery streaming insert — for a real production system you'd use MERGE
        table_ref = f"{_PROJECT}.{_DATASET}.need_clusters"
        row = _flatten_cluster(cluster)
        errors = _bq_client.insert_rows_json(table_ref, [row])
        if errors:
            logger.error("BigQuery insert_rows_json (cluster) errors: %s", errors)
    except Exception as exc:
        logger.error("save_cluster BigQuery error: %s", exc)


async def get_clusters() -> list[dict]:
    """Return all clusters sorted by priority_score descending."""
    if not _BQ_AVAILABLE or _bq_client is None:
        return sorted(
            _clusters_store.values(),
            key=lambda c: c.get("priority_score", 0),
            reverse=True,
        )

    try:
        query = (
            f"SELECT * FROM `{_PROJECT}.{_DATASET}.need_clusters` "
            f"ORDER BY priority_score DESC"
        )
        rows = list(_bq_client.query(query).result())
        result = [dict(r) for r in rows]
        # Refresh in-memory cache
        for r in result:
            _clusters_store[r["id"]] = r
        return result
    except Exception as exc:
        logger.error("get_clusters BigQuery error: %s", exc)
        return sorted(
            _clusters_store.values(),
            key=lambda c: c.get("priority_score", 0),
            reverse=True,
        )


async def get_cluster_by_id(cluster_id: str) -> dict | None:
    """Return a single cluster by ID."""
    if cluster_id in _clusters_store:
        return _clusters_store[cluster_id]

    if not _BQ_AVAILABLE or _bq_client is None:
        return None

    try:
        from google.cloud import bigquery  # type: ignore

        query = (
            f"SELECT * FROM `{_PROJECT}.{_DATASET}.need_clusters` "
            f"WHERE id = @cid LIMIT 1"
        )
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("cid", "STRING", cluster_id)]
        )
        rows = list(_bq_client.query(query, job_config=job_config).result())
        if rows:
            record = dict(rows[0])
            _clusters_store[cluster_id] = record
            return record
        return None
    except Exception as exc:
        logger.error("get_cluster_by_id BigQuery error: %s", exc)
        return _clusters_store.get(cluster_id)


async def update_cluster_field(cluster_id: str, field: str, value: Any) -> None:
    """Update a single field on a cluster (in-memory + BigQuery DML)."""
    if cluster_id in _clusters_store:
        _clusters_store[cluster_id][field] = value

    if not _BQ_AVAILABLE or _bq_client is None:
        return

    try:
        from google.cloud import bigquery  # type: ignore

        query = (
            f"UPDATE `{_PROJECT}.{_DATASET}.need_clusters` "
            f"SET {field} = @val WHERE id = @cid"
        )
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("val", "STRING", str(value)),
                bigquery.ScalarQueryParameter("cid", "STRING", cluster_id),
            ]
        )
        _bq_client.query(query, job_config=job_config).result()
    except Exception as exc:
        logger.error("update_cluster_field BigQuery error: %s", exc)


# ── Private helpers ────────────────────────────────────────────────────────────

def _flatten_submission(s: dict) -> dict:
    """Convert a submission dict to a flat BigQuery-ready row."""
    return {
        "id": s.get("id"),
        "timestamp": s.get("timestamp"),
        "channel": s.get("channel"),
        "text": s.get("text"),
        "category": s.get("category"),
        "location": s.get("location"),
        "lang": s.get("lang"),
        "media_url": s.get("media_url"),
        "lat": s.get("lat"),
        "lng": s.get("lng"),
        "phone_hash": s.get("phone_hash"),
        "ward_id": s.get("ward_id"),
        "authenticity_score": s.get("authenticity_score"),
        "processed": s.get("processed", False),
        "cluster_id": s.get("cluster_id"),
    }


def _flatten_cluster(c: dict) -> dict:
    """Convert a cluster dict to a flat BigQuery-ready row."""
    sb = c.get("score_breakdown", {})
    ev = c.get("evidence", {})
    return {
        "id": c.get("id"),
        "name": c.get("name"),
        "category": c.get("category"),
        "ward_id": c.get("ward_id"),
        "location": c.get("location"),
        "demand_count": c.get("demand_count", 0),
        "priority_score": c.get("priority_score", 0.0),
        "score_D": sb.get("D", 0.0),
        "score_G": sb.get("G", 0.0),
        "score_V": sb.get("V", 0.0),
        "score_F": sb.get("F", 0.0),
        "score_O": sb.get("O", 0.0),
        "evidence_udise": ev.get("udise_ref"),
        "evidence_census": ev.get("census_ref"),
        "evidence_maps": ev.get("maps_ref"),
        "evidence_plan": ev.get("plan_ref"),
        "cost_estimate": c.get("cost_estimate", 0.0),
        "beneficiaries": c.get("beneficiaries", 0),
        "status": c.get("status", "Received"),
        "lat": c.get("lat"),
        "lng": c.get("lng"),
        "last_updated": c.get("last_updated"),
        "submission_ids": json.dumps(c.get("submission_ids", [])),
        "centroid_json": json.dumps(c.get("centroid", [])),
    }


def get_in_memory_clusters() -> dict[str, dict]:
    """Expose the in-memory cluster store (used by agents)."""
    return _clusters_store


def get_in_memory_submissions() -> dict[str, dict]:
    """Expose the in-memory submissions store (used by agents)."""
    return _submissions_store
