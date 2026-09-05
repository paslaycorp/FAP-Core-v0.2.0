"""FAP-Core side of the EPM Assurance Exchange v0.1.

This module deliberately contains only the protocol primitive. It does not
make EPM decisions; it binds a FAP-Core result to the exact request received.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import unicodedata
from datetime import datetime, timezone
from typing import Any, Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

EXCHANGE_VERSION = "0.1"
ENGINE_ID = "fap-core"
POLICY_ID = "fap-core-scoring"
POLICY_VERSION = "v1"
SERVICE_ID_ENV = "FAP_CORE_SERVICE_ID"
PRIVATE_KEY_ENV = "FAP_CORE_ATTESTATION_PRIVATE_KEY"


class AssuranceExchangeError(ValueError):
    """Fail-closed exchange validation error."""


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise AssuranceExchangeError("timestamps must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, (set, frozenset)):
        raise AssuranceExchangeError("unordered collections are not canonical")
    if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
        raise AssuranceExchangeError("non-finite numbers are not canonical")
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise AssuranceExchangeError(f"unsupported canonical value: {type(value).__name__}")


def canonical_bytes(payload: Mapping[str, Any], *, exclude: frozenset[str] = frozenset()) -> bytes:
    if not isinstance(payload, Mapping):
        raise AssuranceExchangeError("payload must be a mapping")
    normalized = _normalize({k: v for k, v in payload.items() if k not in exclude})
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest_hex(payload: Mapping[str, Any], *, exclude: frozenset[str] = frozenset()) -> str:
    return hashlib.sha256(canonical_bytes(payload, exclude=exclude)).hexdigest()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _load_signer() -> tuple[str, Ed25519PrivateKey]:
    service_id = os.getenv(SERVICE_ID_ENV, "").strip()
    encoded = os.getenv(PRIVATE_KEY_ENV, "").strip()
    if not service_id or not encoded:
        raise AssuranceExchangeError("FAP-Core attestation identity is not configured")
    try:
        raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        if len(raw) != 32:
            raise ValueError("Ed25519 private key seed must be 32 bytes")
        return service_id, Ed25519PrivateKey.from_private_bytes(raw)
    except (ValueError, TypeError) as exc:
        raise AssuranceExchangeError("FAP-Core attestation key is invalid") from exc


def verify_request_digest(exchange_request: Mapping[str, Any]) -> None:
    supplied = exchange_request.get("request_digest")
    if not isinstance(supplied, str) or len(supplied) != 64:
        raise AssuranceExchangeError("request digest is missing or malformed")
    expected = digest_hex(exchange_request, exclude=frozenset({"request_digest"}))
    if not __import__("secrets").compare_digest(expected, supplied):
        raise AssuranceExchangeError("request digest mismatch")


def build_attestation(exchange_request: Mapping[str, Any], *, result: Mapping[str, Any], processed_at: datetime) -> dict[str, Any]:
    verify_request_digest(exchange_request)
    service_id, private_key = _load_signer()
    if exchange_request.get("exchange_version") != EXCHANGE_VERSION:
        raise AssuranceExchangeError("unsupported exchange version")
    processed_at = processed_at.astimezone(timezone.utc)
    unsigned = {
        "exchange_version": EXCHANGE_VERSION,
        "request_id": exchange_request["request_id"],
        "nonce": exchange_request["nonce"],
        "request_digest": exchange_request["request_digest"],
        "evidence_id": exchange_request["evidence_id"],
        "artifact_id": result["artifact_id"],
        "engine_id": ENGINE_ID,
        "engine_version": result["engine_version"],
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "oracle_versions": result.get("oracle_versions", []),
        "processed_at": processed_at,
        "result": result["verdict"],
        "confidence": result["confidence"],
        "failure_state": result.get("failure_state"),
        "responder_service_id": service_id,
    }
    response_digest = digest_hex(unsigned)
    signed_payload = {**unsigned, "response_digest": response_digest}
    signature = _b64(private_key.sign(canonical_bytes(signed_payload)))
    return {**signed_payload, "signature": signature}
