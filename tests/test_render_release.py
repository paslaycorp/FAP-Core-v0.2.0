"""Tests for the fail-closed FAP-Core Render production release controller."""
from __future__ import annotations

import json

import pytest
import requests

from ops import render_release
from ops.render_release import (
    DEFAULT_SERVICE_ID,
    EXPECTED_BRANCH,
    EXPECTED_REPO_SLUG,
    EXPECTED_SERVICE,
    EXPECTED_VERSION,
    RenderAPI,
    deploy_commit_sha,
    require_env,
    verify_runtime_health,
    wait_for_live,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.content = json.dumps(payload).encode()

    def raise_for_status(self):
        if self.status_code >= 400:
            response = requests.Response()
            response.status_code = self.status_code
            raise requests.HTTPError("failed", response=response)

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.headers = {}

    def request(self, method, url, **kwargs):
        self.requests.append((method, url, kwargs))
        return self.responses.pop(0)

    def get(self, url, **kwargs):
        self.requests.append(("GET", url, kwargs))
        return self.responses.pop(0)


def test_deploy_commit_sha():
    assert deploy_commit_sha({"commit": {"id": "a" * 40}}) == "a" * 40
    assert deploy_commit_sha(None) is None


def test_render_api_disables_native_autodeploy():
    session = FakeSession([FakeResponse({"autoDeploy": "no"})])
    api = RenderAPI("token", "srv-1", session=session)

    assert api.disable_autodeploy() == {"autoDeploy": "no"}
    method, url, kwargs = session.requests[0]
    assert method == "PATCH"
    assert url.endswith("/services/srv-1")
    assert kwargs["json"] == {"autoDeploy": "no"}


def test_list_deploys_unwraps_render_cursor_shape():
    session = FakeSession(
        [FakeResponse([{"cursor": "abc", "deploy": {"id": "dep-1", "status": "live"}}])]
    )
    api = RenderAPI("token", "srv-1", session=session)
    assert api.list_deploys() == [{"id": "dep-1", "status": "live"}]


def test_wait_for_live_accepts_only_live():
    class API:
        def __init__(self):
            self.states = iter(
                [
                    {"id": "dep-1", "status": "build_in_progress"},
                    {"id": "dep-1", "status": "update_in_progress"},
                    {"id": "dep-1", "status": "live", "commit": {"id": "a" * 40}},
                ]
            )

        def get_deploy(self, deploy_id):
            return next(self.states)

    result = wait_for_live(API(), "dep-1", interval_seconds=0, sleep=lambda _: None)
    assert result["status"] == "live"


def test_wait_for_live_fails_closed_on_terminal_failure():
    class API:
        def get_deploy(self, deploy_id):
            return {"id": deploy_id, "status": "build_failed"}

    with pytest.raises(RuntimeError, match="build_failed"):
        wait_for_live(API(), "dep-1", interval_seconds=0, sleep=lambda _: None)


def test_runtime_health_proves_exact_release_identity():
    sha = "9" * 40
    payload = {
        "status": "healthy",
        "service": EXPECTED_SERVICE,
        "version": EXPECTED_VERSION,
        "git_commit": sha,
        "git_branch": EXPECTED_BRANCH,
        "git_repo_slug": EXPECTED_REPO_SLUG,
        "render_service_id": DEFAULT_SERVICE_ID,
    }
    session = FakeSession([FakeResponse(payload)])

    assert verify_runtime_health(
        "https://example.test/health",
        sha,
        DEFAULT_SERVICE_ID,
        timeout_seconds=1,
        interval_seconds=0,
        session=session,
        sleep=lambda _: None,
    ) == payload


def test_runtime_health_rejects_wrong_sha(monkeypatch):
    wanted = "a" * 40
    payload = {
        "status": "healthy",
        "service": EXPECTED_SERVICE,
        "version": EXPECTED_VERSION,
        "git_commit": "b" * 40,
        "git_branch": EXPECTED_BRANCH,
        "git_repo_slug": EXPECTED_REPO_SLUG,
        "render_service_id": DEFAULT_SERVICE_ID,
    }
    session = FakeSession([FakeResponse(payload)])
    ticks = iter([0.0, 0.0, 2.0])
    monkeypatch.setattr("ops.render_release.time.monotonic", lambda: next(ticks))

    with pytest.raises(RuntimeError, match="commit"):
        verify_runtime_health(
            "https://example.test/health",
            wanted,
            DEFAULT_SERVICE_ID,
            timeout_seconds=1,
            interval_seconds=0,
            session=session,
            sleep=lambda _: None,
        )


def test_require_env_fails_closed_when_secret_missing(monkeypatch):
    monkeypatch.delenv("RENDER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="RENDER_API_KEY"):
        require_env("RENDER_API_KEY")


def test_release_rolls_back_previous_live_deploy_on_proof_failure(monkeypatch):
    previous_sha = "a" * 40
    release_sha = "b" * 40

    class FakeAPI:
        rollback_target = None

        def __init__(self, token, service_id):
            self.service_id = service_id

        def current_live_deploy(self):
            return {"id": "dep-old", "status": "live", "commit": {"id": previous_sha}}

        def get_service(self):
            return {
                "id": DEFAULT_SERVICE_ID,
                "branch": EXPECTED_BRANCH,
                "repo": f"https://github.com/{EXPECTED_REPO_SLUG}",
                "autoDeploy": "no",
            }

        def disable_autodeploy(self):
            return {"autoDeploy": "no"}

        def trigger_deploy(self, commit_sha):
            assert commit_sha == release_sha
            return {"id": "dep-new", "commit": {"id": release_sha}}

        def get_deploy(self, deploy_id):
            if deploy_id == "dep-new":
                return {"id": deploy_id, "status": "live", "commit": {"id": release_sha}}
            if deploy_id == "dep-rollback":
                return {"id": deploy_id, "status": "live", "commit": {"id": previous_sha}}
            raise AssertionError(deploy_id)

        def rollback(self, deploy_id):
            FakeAPI.rollback_target = deploy_id
            return {"id": "dep-rollback"}

    monkeypatch.setenv("RENDER_API_KEY", "test-token")
    monkeypatch.setenv("RELEASE_SHA", release_sha)
    monkeypatch.setenv("RENDER_SERVICE_ID", DEFAULT_SERVICE_ID)
    monkeypatch.setattr(render_release, "RenderAPI", FakeAPI)
    monkeypatch.setattr(
        render_release,
        "verify_runtime_health",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("runtime proof failed")),
    )
    monkeypatch.setattr(render_release, "write_attestation", lambda *args, **kwargs: None)

    with pytest.raises(RuntimeError, match="runtime proof failed"):
        render_release.release()

    assert FakeAPI.rollback_target == "dep-old"
