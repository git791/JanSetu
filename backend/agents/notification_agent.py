"""
Notification Agent.

Delivers status-change notifications to citizens via:
  1. WhatsApp Business API (if WHATSAPP_TOKEN + WHATSAPP_PHONE_ID are set)
  2. Twilio SMS (if TWILIO_* vars are set)
  3. Console stub (local dev fallback)
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
_WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
_WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")
_TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
_TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
_TWILIO_FROM = os.getenv("TWILIO_FROM_NUMBER", "")

_WHATSAPP_API_URL = "https://graph.facebook.com/v19.0/{phone_id}/messages"


async def notify_cluster_status_change(
    cluster_id: str,
    new_status: str,
    citizen_phones: list[str],
) -> dict:
    """
    Notify citizens about a cluster status update.

    Priority order:
      1. WhatsApp Business API
      2. Twilio SMS
      3. Console stub (always succeeds locally)

    Returns:
        {sent: int, failed: int, mode: 'whatsapp' | 'sms' | 'stub'}
    """
    if not citizen_phones:
        logger.info("notify_cluster_status_change: no phones provided, skipping.")
        return {"sent": 0, "failed": 0, "mode": "stub"}

    message = _build_message(cluster_id, new_status)

    if _WHATSAPP_TOKEN and _WHATSAPP_PHONE_ID:
        return await _send_whatsapp(citizen_phones, message)

    if _TWILIO_SID and _TWILIO_TOKEN and _TWILIO_FROM:
        return await _send_sms_twilio(citizen_phones, message)

    return _stub_notify(citizen_phones, message)


# ── WhatsApp Business API ──────────────────────────────────────────────────────

async def _send_whatsapp(phones: list[str], message: str) -> dict:
    url = _WHATSAPP_API_URL.format(phone_id=_WHATSAPP_PHONE_ID)
    headers = {
        "Authorization": f"Bearer {_WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    sent = 0
    failed = 0

    async with httpx.AsyncClient(timeout=15.0) as client:
        for phone in phones:
            payload = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "text",
                "text": {"body": message},
            }
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    sent += 1
                else:
                    logger.warning(
                        "WhatsApp send failed to %s: %s %s",
                        phone,
                        resp.status_code,
                        resp.text,
                    )
                    failed += 1
            except Exception as exc:
                logger.error("WhatsApp send exception for %s: %s", phone, exc)
                failed += 1

    logger.info("WhatsApp: sent=%d failed=%d", sent, failed)
    return {"sent": sent, "failed": failed, "mode": "whatsapp"}


# ── Twilio SMS ────────────────────────────────────────────────────────────────

async def _send_sms_twilio(phones: list[str], message: str) -> dict:
    url = f"https://api.twilio.com/2010-04-01/Accounts/{_TWILIO_SID}/Messages.json"

    sent = 0
    failed = 0

    async with httpx.AsyncClient(
        auth=(_TWILIO_SID, _TWILIO_TOKEN),
        timeout=15.0,
    ) as client:
        for phone in phones:
            try:
                resp = await client.post(
                    url,
                    data={"From": _TWILIO_FROM, "To": phone, "Body": message},
                )
                if resp.status_code in (200, 201):
                    sent += 1
                else:
                    logger.warning(
                        "Twilio send failed to %s: %s %s",
                        phone,
                        resp.status_code,
                        resp.text,
                    )
                    failed += 1
            except Exception as exc:
                logger.error("Twilio send exception for %s: %s", phone, exc)
                failed += 1

    logger.info("Twilio SMS: sent=%d failed=%d", sent, failed)
    return {"sent": sent, "failed": failed, "mode": "sms"}


# ── Console stub ──────────────────────────────────────────────────────────────

def _stub_notify(phones: list[str], message: str) -> dict:
    for phone in phones:
        logger.info("[STUB NOTIFICATION] → %s: %s", phone, message)
    print(f"\n📩 [STUB] Notification to {len(phones)} recipient(s):\n   {message}\n")
    return {"sent": len(phones), "failed": 0, "mode": "stub"}


# ── Message builder ───────────────────────────────────────────────────────────

def _build_message(cluster_id: str, new_status: str) -> str:
    status_messages = {
        "Received": "आपकी शिकायत प्राप्त हो गई है। हम जल्द कार्रवाई करेंगे। (Your complaint has been received.)",
        "Under Review": "आपकी शिकायत की समीक्षा की जा रही है। (Your complaint is under review.)",
        "Approved": "आपकी शिकायत स्वीकृत हो गई है! कार्य जल्द शुरू होगा। (Your complaint has been approved!)",
        "In Progress": "आपकी शिकायत पर कार्य शुरू हो गया है। (Work on your complaint has started.)",
        "Completed": "आपकी शिकायत का समाधान हो गया है। धन्यवाद! (Your complaint has been resolved. Thank you!)",
    }
    detail = status_messages.get(new_status, f"Status updated to: {new_status}")
    return f"JanSetu Update [{cluster_id[-8:].upper()}]: {detail}"
