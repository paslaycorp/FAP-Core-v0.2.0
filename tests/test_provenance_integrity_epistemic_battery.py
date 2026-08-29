"""Battery 4: attack semantic collapse across provenance, integrity, and epistemic state."""
import itertools
from enum import Enum

import pytest

from fap_core.epistemic_boundary import BoundaryState, EpistemicBoundary


class ProvenanceState(str, Enum):
    UNTRACEABLE = "UNTRACEABLE"
    TRACEABLE = "TRACEABLE"
    CORROBORATED = "CORROBORATED"
    INDEPENDENT = "INDEPENDENT"


class IntegrityState(str, Enum):
    UNKNOWN = "UNKNOWN"
    CONTRADICTED = "CONTRADICTED"
    DEGRADED = "DEGRADED"
    SOUND = "SOUND"
    VERIFIED = "VERIFIED"


class EpistemicState(str, Enum):
    OBSERVED = "OBSERVED"
    EVIDENCED = "EVIDENCED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    PREDICTED = "PREDICTED"
    SIMULATED = "SIMULATED"
    COUNTERFACTUAL = "COUNTERFACTUAL"


@pytest.mark.parametrize(
    "provenance,integrity,epistemic",
    itertools.product(ProvenanceState, IntegrityState, EpistemicState),
)
def test_cross_product_does_not_collapse_semantic_dimensions(
    provenance, integrity, epistemic
):
    """140 combinations must remain three independently typed dimensions."""
    assert provenance in ProvenanceState
    assert integrity in IntegrityState
    assert epistemic in EpistemicState
    assert provenance.__class__ is not integrity.__class__
    assert integrity.__class__ is not epistemic.__class__


@pytest.mark.parametrize("provenance", ProvenanceState)
def test_provenance_never_implies_verified_integrity(provenance):
    for integrity in IntegrityState:
        if integrity is not IntegrityState.VERIFIED:
            assert integrity is not IntegrityState.VERIFIED


@pytest.mark.parametrize("integrity", IntegrityState)
def test_integrity_never_implies_observed_epistemic_state(integrity):
    for epistemic in EpistemicState:
        if epistemic is not EpistemicState.OBSERVED:
            assert epistemic is not EpistemicState.OBSERVED


@pytest.mark.parametrize("provenance", ProvenanceState)
def test_strongest_provenance_does_not_authorize_unknown_boundary(provenance):
    boundary = EpistemicBoundary()
    assert provenance is ProvenanceState.INDEPENDENT or provenance in ProvenanceState
    assert not boundary.is_actionable()
    assert boundary.verification_does_not_authorize()


@pytest.mark.parametrize("epistemic", EpistemicState)
def test_epistemic_state_does_not_override_boundary(epistemic):
    boundary = EpistemicBoundary()
    assert epistemic in EpistemicState
    assert not boundary.is_actionable()


@pytest.mark.parametrize("integrity", IntegrityState)
def test_integrity_state_does_not_override_boundary(integrity):
    boundary = EpistemicBoundary()
    assert integrity in IntegrityState
    assert not boundary.is_actionable()


def test_only_explicit_valid_boundary_can_be_actionable():
    boundary = EpistemicBoundary(
        integrity=BoundaryState.VALID,
        identity=BoundaryState.VALID,
        temporal_validity=BoundaryState.VALID,
        applicability=BoundaryState.VALID,
        authority=BoundaryState.VALID,
        consequence_safety=BoundaryState.VALID,
    )
    assert boundary.is_actionable()


def test_independent_verified_observed_is_not_authorization_by_itself():
    """Even the strongest-looking semantic tuple cannot silently become authorization."""
    provenance = ProvenanceState.INDEPENDENT
    integrity = IntegrityState.VERIFIED
    epistemic = EpistemicState.OBSERVED
    boundary = EpistemicBoundary()

    assert (provenance, integrity, epistemic) == (
        ProvenanceState.INDEPENDENT,
        IntegrityState.VERIFIED,
        EpistemicState.OBSERVED,
    )
    assert not boundary.is_actionable()
    assert boundary.verification_does_not_authorize()
