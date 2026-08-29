import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from fap_core.api_models import VerifyRequest

BASE = {
    "timestamp_claimed": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
    "geo": {"lat": 29.7604, "lon": -95.3698},
    "media_hash": "a" * 64,
    "media_type": "image",
    "device": {"model": "test", "manufacturer": "test", "os_version": "1", "enrollment_id": None},
}


def test_sha256_is_exactly_64_hex():
    req = VerifyRequest(**BASE)
    assert len(req.media_hash) == 64


@pytest.mark.parametrize("value", ["abcdefgh", "g" * 64, "a" * 63, "a" * 65])
def test_rejects_non_sha256_hash(value):
    payload = {**BASE, "media_hash": value}
    with pytest.raises(ValidationError):
        VerifyRequest(**payload)


def test_rejects_naive_timestamp():
    payload = {**BASE, "timestamp_claimed": "2026-08-28T12:00:00"}
    with pytest.raises(ValidationError):
        VerifyRequest(**payload)


def test_rejects_future_timestamp():
    payload = {**BASE, "timestamp_claimed": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()}
    with pytest.raises(ValidationError):
        VerifyRequest(**payload)


def test_normalizes_timestamp_to_utc():
    # Fixed historical instant; independent of CI execution time.
    payload = {**BASE, "timestamp_claimed": "2020-01-02T12:00:00-05:00"}
    req = VerifyRequest(**payload)
    assert req.timestamp_claimed.tzinfo is not None
    assert req.timestamp_claimed.utcoffset() == timedelta(0)
