"""Transition battery: prevent unauthorized epistemic/provenance/integrity upgrades."""
from enum import Enum
from itertools import product

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


PROVENANCE_RANK = {s: i for i, s in enumerate(ProvenanceState)}
INTEGRITY_RANK = {s: i for i, s in enumerate(IntegrityState)}
EPISTEMIC_RANK = {s: i for i, s in enumerate(EpistemicState)}


def admissible_upgrade(before, after, *, evidence=False, authority=False):
    """A stronger state requires an explicit transition justification."""
    upgraded = (
        PROVENANCE_RANK[after[0]] > PROVENANCE_RANK[before[0]]
        or INTEGRITY_RANK[after[1]] > INTEGRITY_RANK[before[1]]
        or EPISTEMIC_RANK[after[2]] > EPISTEMIC_RANK[before[2]]
    )
    return not upgraded or (evidence and authority)


@pytest.mark.parametrize("before", product(ProvenanceState, IntegrityState, EpistemicState))
def test_unjustified_self_upgrade_is_rejected(before):
    assert admissible_upgrade(before, before)


@pytest.mark.parametrize("before,after", product(
    product(ProvenanceState, IntegrityState, EpistemicState),
    product(ProvenanceState, IntegrityState, EpistemicState),
))
def test_no_stronger_successor_without_evidence_and_authority(before, after):
    if after != before:
        assert not admissible_upgrade(before, after, evidence=False, authority=False)


@pytest.mark.parametrize("before,after", product(
    product(ProvenanceState, IntegrityState, EpistemicState),
    product(ProvenanceState, IntegrityState, EpistemicState),
))
def test_upgrade_requires_both_evidence_and_authority(before, after):
    if after != before:
        assert not admissible_upgrade(before, after, evidence=True, authority=False)
        assert not admissible_upgrade(before, after, evidence=False, authority=True)


def test_strongest_tuple_cannot_be_created_by_assertion_alone():
    weakest = (
        ProvenanceState.UNTRACEABLE,
        IntegrityState.UNKNOWN,
        EpistemicState.COUNTERFACTUAL,
    )
    strongest = (
        ProvenanceState.INDEPENDENT,
        IntegrityState.VERIFIED,
        EpistemicState.OBSERVED,
    )
    assert not admissible_upgrade(weakest, strongest, evidence=False, authority=False)
    assert not admissible_upgrade(weakest, strongest, evidence=True, authority=False)
    assert not admissible_upgrade(weakest, strongest, evidence=False, authority=True)
    assert admissible_upgrade(weakest, strongest, evidence=True, authority=True)


def test_downgrades_are_not_upgrades():
    strongest = (
        ProvenanceState.INDEPENDENT,
        IntegrityState.VERIFIED,
        EpistemicState.OBSERVED,
    )
    weakest = (
        ProvenanceState.UNTRACEABLE,
        IntegrityState.UNKNOWN,
        EpistemicState.COUNTERFACTUAL,
    )
    assert admissible_upgrade(strongest, weakest)
