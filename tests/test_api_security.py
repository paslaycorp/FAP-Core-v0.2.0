"""API credential configuration and authentication tests."""
import importlib

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


def load_api(monkeypatch, *, env="test", api_key=None):
    monkeypatch.setenv("FAP_ENV", env)
    if api_key is None:
        monkeypatch.delenv("FAP_API_KEY", raising=False)
    else:
        monkeypatch.setenv("FAP_API_KEY", api_key)

    import api
    return importlib.reload(api)


def credentials(value):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=value)


def test_accepts_injected_test_credential(monkeypatch):
    api = load_api(monkeypatch, api_key="test-only-value")
    assert api.verify_key(credentials("test-only-value")) == "test-only-value"


def test_rejects_invalid_credential(monkeypatch):
    api = load_api(monkeypatch, api_key="test-only-value")
    with pytest.raises(HTTPException) as exc:
        api.verify_key(credentials("wrong-test-value"))
    assert exc.value.status_code == 403


def test_rejects_missing_credential(monkeypatch):
    api = load_api(monkeypatch, api_key="test-only-value")
    with pytest.raises(HTTPException) as exc:
        api.verify_key(None)
    assert exc.value.status_code == 403


def test_development_does_not_accept_hardcoded_dev_key(monkeypatch):
    api = load_api(monkeypatch, env="development")
    with pytest.raises(HTTPException) as exc:
        api.verify_key(credentials("dev-key"))
    assert exc.value.status_code == 403


def test_production_fails_closed_without_secret(monkeypatch):
    with pytest.raises(ValueError, match="FAP_API_KEY environment variable must be set in production"):
        load_api(monkeypatch, env="production")
