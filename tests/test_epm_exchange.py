import base64
import hashlib
import os
from datetime import datetime, timezone

from fap_core.epm_exchange import build_attestation, canonical_bytes, digest_hex


def test_canonicalization_matches_sha256():
    payload = {"b": "x", "a": "y"}
    assert digest_hex(payload) == hashlib.sha256(canonical_bytes(payload)).hexdigest()


def test_attestation_binds_exact_verification_input(monkeypatch):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private = Ed25519PrivateKey.generate()
    raw = private.private_bytes_raw()
    monkeypatch.setenv("FAP_EPM_ATTESTATION_PRIVATE_KEY", base64.urlsafe_b64encode(raw).rstrip(b"=").decode())
    monkeypatch.setenv("FAP_EPM_SERVICE_ID", "fap-core")
    verification = {
        "artifact_id": None,
        "timestamp_claimed": datetime(2026, 9, 5, 20, 0, tzinfo=timezone.utc),
        "geo": {"lat": 29.53, "lon": -98.46},
        "media_hash": "a" * 64,
        "media_type": "image",
        "device": {"model": "Phone", "manufacturer": "Example", "os_version": "1", "enrollment_id": None},
        "weather_reported": None,
        "witness_ids": [],
    }
    exchange = {
        "exchange_version": "0.1",
        "request_id": "4f2b8e2f-5b5a-4b2e-9d6b-7e6d7d7d7d01",
        "nonce": "N" * 43,
        "claim_id": "CLM-EX-001",
        "evidence_id": "E-EX-001",
        "media_hash": "a" * 64,
        "timestamp_claimed": verification["timestamp_claimed"],
        "purpose": "claim-verification",
        "scope": "claim",
        "jurisdiction": "TX",
        "rule_id": "carrier-default",
        "rule_version": "1",
        "authority": "carrier-authority",
        "consequence": "critical",
        "requested_at": verification["timestamp_claimed"],
        "requester_service_id": "fap-insurance",
        "verification_input_digest": digest_hex(verification),
    }
    exchange["request_digest"] = digest_hex(exchange)
    attestation = build_attestation(exchange=exchange, verification=verification, result={"artifact_id": "ART-001", "verdict": "STRICT", "confidence": 0.95})
    assert attestation["evidence_id"] == "E-EX-001"
    assert attestation["responder_service_id"] == "fap-core"


def test_attestation_rejects_tampered_exchange(monkeypatch):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    private = Ed25519PrivateKey.generate()
    monkeypatch.setenv("FAP_EPM_ATTESTATION_PRIVATE_KEY", base64.urlsafe_b64encode(private.private_bytes_raw()).rstrip(b"=").decode())
    verification = {"media_hash": "a" * 64}
    exchange = {"exchange_version": "0.1", "request_id": "r", "nonce": "n", "claim_id": "claim", "evidence_id": "e", "media_hash": "a" * 64, "timestamp_claimed": datetime(2026, 9, 5, tzinfo=timezone.utc), "purpose": "p", "scope": "s", "jurisdiction": "TX", "rule_id": "r", "rule_version": "1", "authority": "a", "consequence": "standard", "requested_at": datetime(2026, 9, 5, tzinfo=timezone.utc), "requester_service_id": "epm", "verification_input_digest": digest_hex(verification)}
    exchange["request_digest"] = digest_hex(exchange)
    exchange["purpose"] = "tampered"
    try:
        build_attestation(exchange=exchange, verification=verification, result={"artifact_id": "a", "verdict": "STRICT", "confidence": 1.0})
        assert False, "tampered exchange must be rejected"
    except ValueError as exc:
        assert "request digest" in str(exc)
