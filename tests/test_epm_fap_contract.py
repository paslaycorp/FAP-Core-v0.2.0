from datetime import UTC, datetime, timedelta

import pytest

from fap_core.artifact import Artifact, DeviceStamp, GeoStamp
from fap_core.epm_contract import (
    BoundaryValidation,
    CONTRACT_REVISION_SHA,
    CONTRACT_VERSION,
    EVIDENCE_SCHEMA_VERSION,
    EvidenceAttestation,
    evidence_receipt_from_artifact,
)

AT = datetime(2026, 9, 15, 7, 0, tzinfo=UTC)
SHA = "a" * 40


def _artifact() -> Artifact:
    artifact = Artifact(
        artifact_id="artifact-1",
        created_at=AT,
        media_path="/evidence/item.jpg",
        media_hash="deadbeefcafebabe",
        media_type="image",
        geo=GeoStamp(latitude=29.4, longitude=-98.5),
        device=DeviceStamp(model="sensor", manufacturer="test", os_version="1"),
        claimed_timestamp=AT,
    )
    # Deliberately populate FAP scoring output. The contract receipt must not copy it.
    artifact.final_score = 0.99
    artifact.confidence = 0.98
    artifact.verdict = "STRICT"
    return artifact


def _attestation() -> EvidenceAttestation:
    return EvidenceAttestation(
        attestation_id="attestation-1",
        authority="fap-core-test",
        method="fixture",
        basis="deterministic contract test",
        validated=True,
    )


def _receipt(**overrides):
    kwargs = {
        "observed_at": AT + timedelta(seconds=1),
        "available_at": AT,
        "source": "fap-core-test",
        "attestation": _attestation(),
        "producer_commit_sha": SHA,
    }
    kwargs.update(overrides)
    return evidence_receipt_from_artifact(_artifact(), **kwargs)


def test_receipt_is_bounded_and_does_not_promote_fap_score_or_verdict():
    receipt = _receipt()

    assert receipt["schema_version"] == EVIDENCE_SCHEMA_VERSION
    assert receipt["contract_version"] == CONTRACT_VERSION
    assert receipt["contract_revision_sha"] == CONTRACT_REVISION_SHA
    assert receipt["boundary_validation"]["validated"] is False
    assert receipt["producer"]["commit_sha"] == SHA
    assert "score" not in receipt
    assert "total_score" not in receipt
    assert "confidence" not in receipt
    assert "verdict" not in receipt
    assert "decision" not in receipt
    assert "state" not in receipt


def test_raw_mapping_cannot_self_assert_boundary_validation():
    hostile = {
        "validated": True,
        "validator": "attacker",
        "method": "self-asserted",
        "basis": "because payload says so",
        "validated_at": AT.isoformat(),
    }

    with pytest.raises(TypeError, match="BoundaryValidation"):
        _receipt(boundary_validation=hostile)


def test_typed_boundary_validation_can_be_recorded_explicitly():
    boundary = BoundaryValidation(
        validated=True,
        validator="trusted-ingress",
        method="signed-receipt-verification",
        basis="signature and authority binding verified",
        validated_at=AT + timedelta(seconds=1),
    )

    receipt = _receipt(boundary_validation=boundary)

    assert receipt["boundary_validation"]["validated"] is True
    assert receipt["boundary_validation"]["validator"] == "trusted-ingress"


@pytest.mark.parametrize(
    ("observed_at", "available_at"),
    (
        (datetime(2026, 9, 15, 7, 0), AT),
        (AT, datetime(2026, 9, 15, 7, 0)),
    ),
)
def test_receipt_rejects_timezone_incomparable_times(observed_at, available_at):
    with pytest.raises(ValueError, match="timezone-aware"):
        _receipt(observed_at=observed_at, available_at=available_at)


def test_receipt_rejects_observation_before_availability():
    with pytest.raises(ValueError, match="cannot precede"):
        _receipt(observed_at=AT, available_at=AT + timedelta(seconds=1))


def test_receipt_requires_exact_producer_commit():
    with pytest.raises(ValueError, match="40-character"):
        _receipt(producer_commit_sha="main")


def test_contract_revision_is_exact_hardened_epm_revision():
    assert CONTRACT_REVISION_SHA == "7b20cd45f32c40302388e6cd87c24aa2ab093c5e"
