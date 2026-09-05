"""Minimal EPM Assurance Exchange responder primitives for FAP-Core."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

EXCHANGE_VERSION = "0.1"


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamps must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, (set, frozenset)):
        raise ValueError("unordered collections are not canonical")
    if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
        raise ValueError("non-finite numbers are not canonical")
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise ValueError(f"unsupported canonical value: {type(value).__name__}")


def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(_normalize(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest_hex(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _private_key() -> Ed25519PrivateKey:
    encoded = os.getenv("FAP_EPM_ATTESTATION_PRIVATE_KEY", "")
    if not encoded:
        raise RuntimeError("FAP_EPM_ATTESTATION_PRIVATE_KEY is not configured")
    raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    if len(raw) != 32:
        raise RuntimeError("FAP_EPM_ATTESTATION_PRIVATE_KEY must encode 32 bytes")
    return Ed25519PrivateKey.from_private_bytes(raw)


def build_attestation(*, exchange: Mapping[str, Any], verification: Mapping[str, Any]) -> dict[str, Any]:
    required = ("request_id", "nonce", "request_digest", "verification_input_digest", "evidence_id")
    if any(not isinstance(exchange.get(k), str) or not exchange[k] for k in required):
        raise ValueError("invalid EPM exchange envelope")
    expected_input = exchange["verification_input_digest"]
    actual_input = digest_hex(verification)
    if actual_input != expected_input:
        raise ValueError("verification input digest mismatch")
    responder = os.getenv("FAP_EPM_SERVICE_ID", "fap-core")
    engine_version = os.getenv("FAP_EPM_ENGINE_VERSION", "0.2.0")
    policy_id = os.getenv("FAP_EPM_POLICY_ID", "fap-core-default")
    policy_version = os.getenv("FAP_EPM_POLICY_VERSION", "1")
    processed_at = datetime.now(timezone.utc)
    unsigned = {
        "exchange_version": EXCHANGE_VERSION,
        "request_id": exchange["request_id"],
        "nonce": exchange["nonce"],
        "request_digest": exchange["request_digest"],
        "evidence_id": exchange["evidence_id"],
        "artifact_id": verification["artifact_id"],
        "engine_id": responder,
        "engine_version": engine_version,
        "policy_id": policy_id,
        "policy_version": policy_version,
        "oracle_versions": ["fap-core:internal-v1"],
        "processed_at": processed_at,
        "result": verification["verdict"],
        "confidence": verification["confidence"],
        "failure_state": None,
        "responder_service_id": responder,
    }
    response_digest = digest_hex(unsigned)
    signature = _private_key().sign(canonical_bytes(unsigned | {"response_digest": response_digest}))
    return {**unsigned, "response_digest": response_digest, "signature": _b64(signature)}
