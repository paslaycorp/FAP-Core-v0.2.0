from fap_core.epistemic_boundary import BoundaryState, EpistemicBoundary


def test_verification_does_not_authorize():
    state = EpistemicBoundary(
        integrity=BoundaryState.VALID,
        identity=BoundaryState.VALID,
        temporal_validity=BoundaryState.VALID,
    )
    assert state.verification_does_not_authorize()
    assert not state.is_actionable()


def test_valid_components_require_explicit_applicability_authority_and_safety():
    state = EpistemicBoundary(
        integrity=BoundaryState.VALID,
        identity=BoundaryState.VALID,
        temporal_validity=BoundaryState.VALID,
        applicability=BoundaryState.VALID,
        authority=BoundaryState.VALID,
        consequence_safety=BoundaryState.VALID,
    )
    assert state.is_actionable()


def test_invalid_applicability_blocks_action():
    state = EpistemicBoundary(
        integrity=BoundaryState.VALID,
        identity=BoundaryState.VALID,
        temporal_validity=BoundaryState.VALID,
        applicability=BoundaryState.INVALID,
        authority=BoundaryState.VALID,
        consequence_safety=BoundaryState.VALID,
    )
    assert not state.is_actionable()
