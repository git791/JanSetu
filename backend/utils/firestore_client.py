"""
Firebase Admin / Firestore client wrapper.

Provides real-time submission storage and cluster status updates via Firestore.
Falls back to an in-memory list when Firebase is not configured.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ── In-memory fallback ────────────────────────────────────────────────────────
_mem_submissions: list[dict] = []
_mem_clusters: dict[str, dict] = {}

# ── Firebase state ─────────────────────────────────────────────────────────────
_db = None
_FIREBASE_AVAILABLE = False


def init_firestore() -> None:
    """Attempt to initialise Firebase Admin SDK + Firestore client."""
    global _db, _FIREBASE_AVAILABLE

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT", "")

    if not service_account_path:
        logger.warning(
            "FIREBASE_SERVICE_ACCOUNT not set — Firestore using in-memory fallback."
        )
        return

    if not os.path.exists(service_account_path):
        logger.warning(
            "Firebase service account file '%s' not found — using in-memory fallback.",
            service_account_path,
        )
        return

    try:
        import firebase_admin  # type: ignore
        from firebase_admin import credentials, firestore  # type: ignore

        # Only initialise once even if called multiple times
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)

        _db = firestore.client()
        _FIREBASE_AVAILABLE = True
        logger.info("Firestore client initialised.")
    except Exception as exc:
        logger.warning("Failed to init Firebase: %s — using in-memory fallback.", exc)


# ── Submissions ────────────────────────────────────────────────────────────────

async def save_submission_realtime(submission: dict) -> None:
    """
    Persist a submission to Firestore's `submissions` collection.
    Also mirrors it to the in-memory store.
    """
    _mem_submissions.append(submission)

    if not _FIREBASE_AVAILABLE or _db is None:
        return

    try:
        doc_ref = _db.collection("submissions").document(submission["id"])
        doc_ref.set(submission)
    except Exception as exc:
        logger.error("save_submission_realtime Firestore error: %s", exc)


async def update_cluster_status(cluster_id: str, status: str) -> None:
    """
    Update the status field of a cluster in Firestore's `need_clusters` collection.
    """
    if cluster_id in _mem_clusters:
        _mem_clusters[cluster_id]["status"] = status

    if not _FIREBASE_AVAILABLE or _db is None:
        return

    try:
        doc_ref = _db.collection("need_clusters").document(cluster_id)
        doc_ref.update({"status": status})
    except Exception as exc:
        logger.error("update_cluster_status Firestore error: %s", exc)


async def save_cluster_realtime(cluster: dict) -> None:
    """Persist / overwrite a cluster document in Firestore."""
    _mem_clusters[cluster["id"]] = cluster

    if not _FIREBASE_AVAILABLE or _db is None:
        return

    try:
        doc_ref = _db.collection("need_clusters").document(cluster["id"])
        doc_ref.set(cluster)
    except Exception as exc:
        logger.error("save_cluster_realtime Firestore error: %s", exc)


async def get_submission_stream() -> list[dict]:
    """
    Return all submissions currently stored.

    In production this would be replaced by a Firestore real-time listener;
    for MVP / REST polling this returns a snapshot.
    """
    if not _FIREBASE_AVAILABLE or _db is None:
        return list(_mem_submissions)

    try:
        docs = _db.collection("submissions").stream()
        return [doc.to_dict() for doc in docs]
    except Exception as exc:
        logger.error("get_submission_stream Firestore error: %s", exc)
        return list(_mem_submissions)


async def get_cluster_realtime(cluster_id: str) -> dict | None:
    """Return a single cluster from Firestore (or in-memory fallback)."""
    if not _FIREBASE_AVAILABLE or _db is None:
        return _mem_clusters.get(cluster_id)

    try:
        doc = _db.collection("need_clusters").document(cluster_id).get()
        return doc.to_dict() if doc.exists else None
    except Exception as exc:
        logger.error("get_cluster_realtime Firestore error: %s", exc)
        return _mem_clusters.get(cluster_id)
