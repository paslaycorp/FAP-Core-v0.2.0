"""Transition battery: exercise the repository's actual epistemic boundary contract."""
import itertools

from fap_core.epistemic_boundary import BoundaryState, EpistemicBoundary

FIELDS = (
    "integrity",
    "identity",
    "temporal_validity",
    "applicability",
    "authority",
    "consequence_safety",
)


def make_state(values):
    return EpistemicBoundary(**dict(zip(FIELDS, values)))


def test_exhaustive_successor_cannot_bypass_actual_boundary():
    """729 real boundary states: only all-VALID is actionable."""
    for values in itertools.product(
        (BoundaryState.UNKNOWN, BoundaryState.VALID, BoundaryState.INVALID),
        repeat=len(FIELDS),
    ):
        state = make_state(values)
        expected = all(value is BoundaryState.VALID for value in values)
        assert state.is_actionable() is expected


def test_single_dimension_breach_blocks_action():
    for field in FIELDS:
        state = make_state([BoundaryState.VALID] * len(FIELDS))
        setattr(state, field, BoundaryState.UNKNOWN)
        assert not state.is_actionable()
        setattr(state, field, BoundaryState.INVALID)
        assert not state.is_actionable()


def test_recovery_requires_restoring_breached_dimension():
    state = make_state([BoundaryState.VALID] * len(FIELDS))
    state.integrity = BoundaryState.INVALID
    assert not state.is_actionable()
    state.integrity = BoundaryState.VALID
    assert state.is_actionable()


def test_verification_never_becomes_authorization_with_missing_authority():
    state = make_state([BoundaryState.VALID] * len(FIELDS))
    state.authority = BoundaryState.UNKNOWN
    assert state.verification_does_not_authorize()
    assert not state.is_actionable()


def test_verification_never_becomes_authorization_with_invalid_authority():
    state = make_state([BoundaryState.VALID] * len(FIELDS))
    state.authority = BoundaryState.INVALID
    assert state.verification_does_not_authorize()
    assert not state.is_actionable()


def test_valid_boundary_is_actionable():
    state = make_state([BoundaryState.VALID] * len(FIELDS))
    assert state.is_actionable()
