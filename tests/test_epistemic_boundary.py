import pytest

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
