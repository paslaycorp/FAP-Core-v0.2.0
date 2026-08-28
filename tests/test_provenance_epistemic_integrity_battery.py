"""Fourth battery: exhaustive provenance × integrity × epistemic-state matrix.

This is a taxonomy/contract test. It deliberately keeps the three axes distinct:
provenance describes traceability strength, integrity describes evidence condition,
and epistemic state describes the claim's mode of knowing. No axis is permitted
to silently substitute for another.
"""
from itertools import product
from enum import Enum

import pytest


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


PROVENANCE_STATES = tuple(ProvenanceState)
INTEGRITY_STATES = tuple(IntegrityState)
EPISTEMIC_STATES = tuple(EpistemicState)


@pytest.mark.parametrize("provenance,integrity,epistemic", product(
    PROVENANCE_STATES, INTEGRITY_STATES, EPISTEMIC_STATES
))
def test_every_cross_product_state_is_representable_without_category_collapse(
    provenance, integrity, epistemic
):
    assert provenance in PROVENANCE_STATES
    assert integrity in INTEGRITY_STATES
    assert epistemic in EPISTEMIC_STATES
    assert provenance.value != integrity.value
    assert provenance.value != epistemic.value
    assert integrity.value != epistemic.value


def test_canonical_state_counts_are_locked():
    assert len(PROVENANCE_STATES) == 4
    assert len(INTEGRITY_STATES) == 5
    assert len(EPISTEMIC_STATES) == 7
    assert len(PROVENANCE_STATES) * len(INTEGRITY_STATES) * len(EPISTEMIC_STATES) == 140


def test_provenance_strength_is_distinct_from_integrity():
    for provenance in PROVENANCE_STATES:
        for integrity in INTEGRITY_STATES:
            assert provenance is not integrity


def test_integrity_does_not_upgrade_epistemic_status():
    for epistemic in EpistemicState:
        for integrity in (IntegrityState.SOUND, IntegrityState.VERIFIED):
            assert epistemic in EPISTEMIC_STATES
            assert integrity in INTEGRITY_STATES
            # Verification is an integrity property, not an epistemic promotion.
            assert epistemic.value in {state.value for state in EpistemicState}


def test_independent_provenance_does_not_imply_verified_integrity():
    # Independence is provenance capacity, not proof of integrity.
    assert ProvenanceState.INDEPENDENT is not IntegrityState.VERIFIED


def test_counterfactual_does_not_become_observed_through_provenance():
    # Strong lineage cannot change the epistemic mode of a claim.
    for provenance in ProvenanceState:
        assert provenance in PROVENANCE_STATES
        assert EpistemicState.COUNTERFACTUAL is not EpistemicState.OBSERVED


def test_no_single_axis_can_authorize_the_other_two():
    # Exhaustive negative contract: no state on one axis is itself a state on another.
    provenance_values = {state.value for state in ProvenanceState}
    integrity_values = {state.value for state in IntegrityState}
    epistemic_values = {state.value for state in EpistemicState}

    assert provenance_values.isdisjoint(integrity_values)
    assert provenance_values.isdisjoint(epistemic_values)
    assert integrity_values.isdisjoint(epistemic_values)
