"""Hard-boundary adversarial tests for VerifyClaimRequest.

These tests intentionally attack the request boundary with malformed, ambiguous,
oversized, and internally inconsistent inputs. The contract is fail-closed:
invalid evidence never reaches verification logic.
"""
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from fap_insurance.api import VerifyClaimRequest


NOW = datetime.now(timezone.utc)


def valid_payload(**overrides):
    payload = {
        "claim_id": "CLM-123456",
        "media_url": "https://example.com/evidence.jpg",
        "media_hash": "a" * 64,
        "lat": 29.4241,
        "lon": -98.4936,
        "timestamp_claimed": NOW,
        "device_model": "SM-A156U",
        "device_manufacturer": "Samsung",
        "device_os": "Android 16",
        "enrollment_id": "device-123",
        "witness_ids": ["w-001", "w-002"],
        "policy_number": "POL-123456",
        "adjuster_notes": "Observed damage at inspection site.",
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("field,value", [
    ("lat", None),
    ("lat", "north"),
    ("lat", 90.000001),
    ("lat", -90.000001),
    ("lon", None),
    ("lon", "west"),
    ("lon", 180.000001),
    ("lon", -180.000001),
    ("lat", float("inf")),
    ("lon", float("-inf")),
    ("lat", float("nan")),
    ("lon", float("nan")),
])
def test_coordinates_are_hard_bounded(field, value):
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(**{field: value}))


def test_null_island_is_rejected():
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(lat=0.0, lon=0.0))


@pytest.mark.parametrize("timestamp", [
    "yesterday",
    "tomorrow",
    "2026-01-01",
    "not-a-timestamp",
])
def test_timestamp_must_be_timezone_aware_iso_datetime(timestamp):
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(timestamp_claimed=timestamp))


def test_naive_datetime_is_rejected():
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(timestamp_claimed=datetime(2026, 1, 1, 12, 0, 0)))


def test_future_timestamp_is_rejected():
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(timestamp_claimed=datetime.now(timezone.utc) + timedelta(seconds=5)))


@pytest.mark.parametrize("media_hash", [
    "",
    "abc",
    "g" * 64,
    "a" * 63,
    "a" * 65,
])
def test_supplied_media_hash_must_be_sha256(media_hash):
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(media_hash=media_hash))


def test_media_hash_is_normalized_to_lowercase():
    request = VerifyClaimRequest(**valid_payload(media_hash="ABCDEF0123456789" * 4))
    assert request.media_hash == "abcdef0123456789" * 4


@pytest.mark.parametrize("url", [
    "javascript:alert(1)",
    "file:///etc/passwd",
    "ftp://example.com/evidence.jpg",
    "not-a-url",
])
def test_media_url_rejects_unsafe_or_malformed_schemes(url):
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(media_url=url))


def test_witness_ids_must_be_unique():
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(witness_ids=["w-001", "w-001"]))


def test_witness_ids_have_hard_cardinality_limit():
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(witness_ids=[f"w-{i:03d}" for i in range(11)]))


@pytest.mark.parametrize("witness_ids", [[""], ["   "], [None]])
def test_witness_ids_cannot_be_blank_or_null(witness_ids):
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(witness_ids=witness_ids))


@pytest.mark.parametrize("field", ["claim_id", "device_model", "device_manufacturer", "device_os"])
def test_required_identity_fields_cannot_be_blank(field):
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(**{field: "   "}))


def test_claim_id_has_upper_length_bound():
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(claim_id="C" * 257))


def test_policy_number_has_upper_length_bound():
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(policy_number="P" * 257))


def test_adjuster_notes_has_upper_length_bound():
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(adjuster_notes="N" * 4001))


def test_media_url_has_upper_length_bound():
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(media_url="https://example.com/" + "x" * 4096))


def test_extra_fields_are_rejected():
    with pytest.raises(ValidationError):
        VerifyClaimRequest(**valid_payload(attacker_controlled_score=1.0))


def test_valid_boundary_coordinates_are_accepted():
    VerifyClaimRequest(**valid_payload(lat=90.0, lon=180.0))
    VerifyClaimRequest(**valid_payload(lat=-90.0, lon=-180.0))


def test_default_witnesses_are_empty_list():
    payload = valid_payload()
    payload.pop("witness_ids")
    request = VerifyClaimRequest(**payload)
    assert request.witness_ids == []
