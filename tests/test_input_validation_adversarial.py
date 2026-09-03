import pytest
from pydantic import ValidationError

from fap_insurance.api import VerifyClaimRequest


def valid_payload(**overrides):
    payload = {
        "claim_id": "CLM-001",
        "media_url": "https://example.com/media.jpg",
        "media_hash": "a" * 64,
        "lat": 29.4241,
        "lon": -98.4936,
        "timestamp_claimed": "2026-09-01T12:00:00Z",
        "device_model": "Test Device",
        "device_manufacturer": "Test Manufacturer",
        "device_os": "Android",
        "enrollment_id": "ENR-001",
        "witness_ids": ["W-001"],
    }
    payload.update(overrides)
    return payload


def assert_invalid(**overrides):
    with pytest.raises((ValidationError, ValueError)):
        VerifyClaimRequest(**valid_payload(**overrides))


@pytest.mark.parametrize("lat", [None, "not-a-number", 500, -500])
def test_invalid_latitude_rejected(lat):
    assert_invalid(lat=lat)


@pytest.mark.parametrize("lon", [None, "", "not-a-number", 999, -999])
def test_invalid_longitude_rejected(lon):
    assert_invalid(lon=lon)


def test_future_timestamp_rejected():
    assert_invalid(timestamp_claimed="2099-01-01T00:00:00Z")


@pytest.mark.parametrize("media_hash", ["", "abc", "g" * 64, "a" * 63, "a" * 65])
def test_invalid_media_hash_rejected(media_hash):
    assert_invalid(media_hash=media_hash)


def test_duplicate_witness_ids_rejected():
    assert_invalid(witness_ids=["W-001", "W-001"])


def test_more_than_10_witness_ids_rejected():
    assert_invalid(witness_ids=[f"W-{i:03d}" for i in range(11)])


def test_blank_witness_id_rejected():
    assert_invalid(witness_ids=[" "])


def test_policy_number_over_64_characters_rejected():
    assert_invalid(policy_number="P" * 65)


def test_adjuster_notes_over_2000_characters_rejected():
    assert_invalid(adjuster_notes="N" * 2001)
