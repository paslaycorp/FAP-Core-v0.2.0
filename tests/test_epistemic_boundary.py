import pytest

from fap_core.artifact import Artifact, ArtifactStatus
from fap_core.epistemic_boundary import BoundaryState, EpistemicBoundary


def fully_valid_boundary() -> EpistemicBoundary:
    return EpistemicBoundary(
        integrity=BoundaryState.VALID,
        identity=BoundaryState.VALID,
        temporal_validity=BoundaryState.VALID,
        applicability=BoundaryState.VALID,
        authority=BoundaryState.VALID,
        consequence_safety=BoundaryState.VALID,
    )


def test_verification_does_not_authorize_when_authority_unknown():
    state = fully_valid_boundary()
    state.authority = BoundaryState.UNKNOWN
    assert state.verification_does_not_authorize()
    assert not state.is_actionable()


def test_verification_does_not_authorize_when_authority_invalid():
    state = fully_valid_boundary()
    state.authority = BoundaryState.INVALID
    assert state.verification_does_not_authorize()
    assert not state.is_actionable()


@pytest.mark.parametrize(
    "field",
    [
        "integrity",
        "identity",
        "temporal_validity",
        "applicability",
        "authority",
        "consequence_safety",
    ],
)
def test_any_non_valid_boundary_state_blocks_action(field):
    state = fully_valid_boundary()
    setattr(state, field, BoundaryState.INVALID)
    assert not state.is_actionable()


@pytest.mark.parametrize(
    "field",
    [
        "integrity",
        "identity",
        "temporal_validity",
        "applicability",
        "authority",
        "consequence_safety",
    ],
)
def test_any_unknown_boundary_state_blocks_action(field):
    state = fully_valid_boundary()
    setattr(state, field, BoundaryState.UNKNOWN)
    assert not state.is_actionable()


def test_all_explicitly_valid_components_are_actionable():
    assert fully_valid_boundary().is_actionable()


def test_verified_artifact_does_not_bypass_unknown_boundary():
    artifact = Artifact.from_capture(
        media_path="evidence.jpg",
        media_hash="a" * 64,
        media_type="image/jpeg",
        latitude=27.8006,
        longitude=-97.3964,
        device_model="test",
        device_manufacturer="test",
        os_version="test",
    )
    artifact.status = ArtifactStatus.VERIFIED
    boundary = EpistemicBoundary()

    assert artifact.status is ArtifactStatus.VERIFIED
    assert not boundary.is_actionable()
    assert boundary.verification_does_not_authorize()


def test_high_score_verification_does_not_bypass_boundary():
    artifact = Artifact.from_capture(
        media_path="evidence.jpg",
        media_hash="b" * 64,
        media_type="image/jpeg",
        latitude=27.8006,
        longitude=-97.3964,
        device_model="test",
        device_manufacturer="test",
        os_version="test",
    )
    artifact.set_score(
        total=1.0,
        verdict="STRICT",
        components={"verification": 1.0},
        confidence=1.0,
        audit=[],
    )
    artifact.finalize()
    boundary = EpistemicBoundary()

    assert artifact.final_score == 1.0
    assert artifact.status is ArtifactStatus.VERIFIED
    assert not boundary.is_actionable()


def test_boundary_requires_explicit_authority_even_when_everything_else_is_valid():
    state = fully_valid_boundary()
    state.authority = BoundaryState.UNKNOWN
    assert not state.is_actionable()
    assert state.verification_does_not_authorize()
