"""EPM-FAP Contract v1 evidence-receipt adapter.

FAP-Core produces evidence. It does not execute EPM and does not acquire EPM
transition authority by emitting this receipt. Scores, confidence, and verdicts
are deliberately excluded from the canonical receipt.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .artifact import Artifact

CONTRACT_VERSION = "epm-fap-assurance/1.0"
CONTRACT_REVISION_SHA = "7b20cd45f32c40302388e6cd87c24aa2ab093c5e"
EVIDENCE_SCHEMA_VERSION = "epm-fap-evidence-receipt/1.0"
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _require_aware(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


@dataclass(frozen=True)
class EvidenceAttestation:
    attestation_id: str
    authority: str
    method: str
    basis: str
    validated: bool

    def __post_init__(self) -> None:
        for field in ("attestation_id", "authority", "method", "basis"):
            _require_text(getattr(self, field), field)

    def as_receipt(self) -> dict[str, Any]:
        return {
            "attestation_id": self.attestation_id,
            "authority": self.authority,
            "method": self.method,
            "basis": self.basis,
            "validated": self.validated,
        }


@dataclass(frozen=True)
class BoundaryValidation:
    validated: bool
    validator: str
    method: str
    basis: str
    validated_at: datetime

    def __post_init__(self) -> None:
        for field in ("validator", "method", "basis"):
            _require_text(getattr(self, field), field)
        _require_aware(self.validated_at, "validated_at")

    def as_receipt(self) -> dict[str, Any]:
        return {
            "validated": self.validated,
            "validator": self.validator,
            "method": self.method,
            "basis": self.basis,
            "validated_at": self.validated_at.isoformat(),
        }


def evidence_receipt_from_artifact(
    artifact: Artifact,
    *,
    observed_at: datetime,
    available_at: datetime,
    source: str,
    attestation: EvidenceAttestation,
    producer_commit_sha: str,
    boundary_validation: BoundaryValidation | None = None,
    producer_component: str = "fap-core",
    producer_repository: str = "paslaycorp/FAP-Core-v0.2.0",
) -> dict[str, Any]:
    """Create a bounded Evidence Receipt without promoting FAP scores to authority.

    Boundary validation is accepted only as the typed ``BoundaryValidation``
    result supplied by trusted in-process code. Raw mappings are rejected.
    When no boundary decision is supplied the receipt records an explicit
    unvalidated state rather than assuming trust.
    """
    if not isinstance(artifact, Artifact):
        raise TypeError("artifact must be an Artifact")
    if not isinstance(attestation, EvidenceAttestation):
        raise TypeError("attestation must be an EvidenceAttestation")
    if boundary_validation is not None and not isinstance(
        boundary_validation, BoundaryValidation
    ):
        raise TypeError("boundary_validation must be a BoundaryValidation")

    _require_aware(observed_at, "observed_at")
    _require_aware(available_at, "available_at")
    if observed_at < available_at:
        raise ValueError("observed_at cannot precede available_at")

    _require_text(source, "source")
    _require_text(producer_component, "producer_component")
    _require_text(producer_repository, "producer_repository")
    if not _SHA40.fullmatch(producer_commit_sha):
        raise ValueError("producer_commit_sha must be an exact 40-character lowercase SHA")

    boundary = boundary_validation or BoundaryValidation(
        validated=False,
        validator=producer_component,
        method="not-evaluated",
        basis="no independent ingestion-boundary validation supplied",
        validated_at=observed_at,
    )
    provenance_ref = artifact.provenance_hash()
    receipt_material = (
        f"{artifact.artifact_id}:{provenance_ref}:{observed_at.isoformat()}:"
        f"{producer_commit_sha}:{CONTRACT_VERSION}:{CONTRACT_REVISION_SHA}"
    )
    receipt_id = "fap-evidence:" + hashlib.sha256(receipt_material.encode()).hexdigest()

    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "contract_revision_sha": CONTRACT_REVISION_SHA,
        "receipt_id": receipt_id,
        "evidence_id": artifact.artifact_id,
        "source": source,
        "provenance_ref": provenance_ref,
        "observed_at": observed_at.isoformat(),
        "available_at": available_at.isoformat(),
        "attestation": attestation.as_receipt(),
        "boundary_validation": boundary.as_receipt(),
        "producer": {
            "component": producer_component,
            "repository": producer_repository,
            "commit_sha": producer_commit_sha,
        },
    }
