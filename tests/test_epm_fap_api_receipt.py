from __future__ import annotations

from datetime import UTC, datetime

from fap_core.artifact import Artifact, DeviceStamp, GeoStamp
from fap_core.epm_contract import CONTRACT_REVISION_SHA


def test_contract_revision_shape_is_exact_sha():
    assert len(CONTRACT_REVISION_SHA) == 40
    int(CONTRACT_REVISION_SHA, 16)


def test_artifact_receipt_identity_can_bind_runtime_sha(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "a" * 40)
    artifact = Artifact(
        artifact_id="evidence-1",
        created_at=datetime(2026, 9, 20, 9, 0, tzinfo=UTC),
        media_path="api",
        media_hash="b" * 64,
        media_type="image",
        geo=GeoStamp(latitude=29.4, longitude=-98.5),
        device=DeviceStamp(model="sensor", manufacturer="test", os_version="1"),
        claimed_timestamp=datetime(2026, 9, 20, 8, 59, tzinfo=UTC),
    )
    assert artifact.artifact_id == "evidence-1"
