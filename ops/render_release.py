"""Fail-closed production release controller for FAP-Core on Render.

Deploy exactly one authorized Git SHA, prove that Render made that SHA live,
prove the running service self-identifies as the same release, write a
machine-readable attestation, and roll back to the previously live deploy if
release proof fails.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

API_BASE = "https://api.render.com/v1"
DEFAULT_SERVICE_ID = "srv-da8rfv8ae00c73bka16g"
DEFAULT_HEALTH_URL = "https://fap-core-odm4.onrender.com/health"
DEFAULT_IDENTITY_URL = "https://fap-core-odm4.onrender.com/auth/check"
EXPECTED_REPO_SLUG = "paslaycorp/FAP-Core-v0.2.0"
EXPECTED_BRANCH = "main"
EXPECTED_SERVICE = "fap-core"
EXPECTED_VERSION = "0.2.0"
EXPECTED_ENVIRONMENT = "production"
TERMINAL_FAILURES = {
    "build_failed",
    "canceled",
    "cancelled",
    "deactivated",
    "pre_deploy_failed",
    "update_failed",
}


@dataclass
class ReleaseAttestation:
    schema_version: str
    release_sha: str
    expected_repo_slug: str
    expected_branch: str
    expected_service: str
    expected_version: str
    render_service_id: str
    previous_live_deploy_id: str | None
    previous_live_sha: str | None
    render_deploy_id: str | None
    render_deploy_sha: str | None
    render_status: str | None
    runtime_health: dict[str, Any] | None
    workflow_url: str | None
    verified_at: str
    result: str
    rollback_deploy_id: str | None = None
    rollback_status: str | None = None
    rollback_runtime_health: dict[str, Any] | None = None
    failure: str | None = None


class RenderAPI:
    def __init__(
        self,
        token: str,
        service_id: str,
        *,
        session: requests.Session | None = None,
    ) -> None:
        self.service_id = service_id
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def _request(self, method: str, path: str, **kwargs) -> Any:
        response = self.session.request(
            method,
            f"{API_BASE}{path}",
            timeout=30,
            **kwargs,
        )
        response.raise_for_status()
        return response.json() if response.content else None

    def get_service(self) -> dict[str, Any]:
        return self._request("GET", f"/services/{self.service_id}")

    def disable_autodeploy(self) -> dict[str, Any] | None:
        return self._request(
            "PATCH",
            f"/services/{self.service_id}",
            json={"autoDeploy": "no"},
        )

    @staticmethod
    def _unwrap_deploy(item: dict[str, Any]) -> dict[str, Any]:
        deploy = item.get("deploy")
        return deploy if isinstance(deploy, dict) else item

    def list_deploys(self, limit: int = 20) -> list[dict[str, Any]]:
        payload = self._request(
            "GET",
            f"/services/{self.service_id}/deploys",
            params={"limit": limit},
        )
        if not isinstance(payload, list):
            raise TypeError("Render deploy list returned a non-list payload")
        return [self._unwrap_deploy(item) for item in payload]

    def current_live_deploy(self) -> dict[str, Any] | None:
        for deploy in self.list_deploys():
            if deploy.get("status") == "live":
                return deploy
        return None

    def trigger_deploy(self, commit_sha: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/services/{self.service_id}/deploys",
            json={"commitId": commit_sha},
        )

    def get_deploy(self, deploy_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/services/{self.service_id}/deploys/{deploy_id}",
        )

    def rollback(self, deploy_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/services/{self.service_id}/rollback",
            json={"deployId": deploy_id},
        )


def deploy_commit_sha(deploy: dict[str, Any] | None) -> str | None:
    if not deploy:
        return None
    commit = deploy.get("commit") or {}
    return commit.get("id")


def wait_for_live(
    api: RenderAPI,
    deploy_id: str,
    *,
    timeout_seconds: int = 900,
    interval_seconds: int = 10,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        deploy = api.get_deploy(deploy_id)
        status = str(deploy.get("status", "unknown"))
        if status == "live":
            return deploy
        if status in TERMINAL_FAILURES or status.endswith("_failed"):
            raise RuntimeError(f"Render deploy {deploy_id} failed with status {status}")
        sleep(interval_seconds)
    raise TimeoutError(f"Render deploy {deploy_id} did not become live before timeout")


def verify_runtime_health(
    identity_url: str,
    release_sha: str,
    service_id: str,
    api_key: str,
    *,
    timeout_seconds: int = 300,
    interval_seconds: int = 10,
    session: requests.Session | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    http = session or requests.Session()
    deadline = time.monotonic() + timeout_seconds
    last_problem = "no response"

    while time.monotonic() < deadline:
        try:
            response = http.get(
                identity_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Cache-Control": "no-cache",
                },
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            checks = {
                "status": data.get("status") == "healthy",
                "service": data.get("service") == EXPECTED_SERVICE,
                "version": data.get("version") == EXPECTED_VERSION,
                "commit": data.get("git_commit") == release_sha,
                "branch": data.get("git_branch") == EXPECTED_BRANCH,
                "repo": data.get("git_repo_slug") == EXPECTED_REPO_SLUG,
                "render_service_id": data.get("render_service_id") == service_id,
                "environment": data.get("environment") == EXPECTED_ENVIRONMENT,
            }
            if all(checks.values()):
                return data
            failed = [name for name, ok in checks.items() if not ok]
            last_problem = f"health proof mismatch: {', '.join(failed)}; payload={data}"
        except Exception as exc:  # noqa: BLE001 - startup/transport retries are intentional
            last_problem = str(exc)
        sleep(interval_seconds)

    raise RuntimeError(f"Runtime health could not prove release {release_sha}: {last_problem}")


def verify_rollback_health(
    health_url: str,
    expected_sha: str,
    service_id: str,
    *,
    timeout_seconds: int = 120,
    interval_seconds: int = 10,
    session: requests.Session | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Prove the rolled-back endpoint is actually serving the prior release SHA."""
    http = session or requests.Session()
    deadline = time.monotonic() + timeout_seconds
    last_problem = "no response"

    while time.monotonic() < deadline:
        try:
            response = http.get(
                health_url,
                headers={"Cache-Control": "no-cache"},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            checks = {
                "status": data.get("status") == "healthy",
                "service": data.get("service") == EXPECTED_SERVICE,
                "commit": data.get("git_commit") == expected_sha,
                "branch": data.get("git_branch") == EXPECTED_BRANCH,
                "repo": data.get("git_repo_slug") == EXPECTED_REPO_SLUG,
                "render_service_id": data.get("render_service_id") == service_id,
            }
            if all(checks.values()):
                return data
            failed = [name for name, ok in checks.items() if not ok]
            last_problem = f"rollback health mismatch: {', '.join(failed)}; payload={data}"
        except Exception as exc:  # noqa: BLE001 - bounded rollback proof retry
            last_problem = str(exc)
        sleep(interval_seconds)

    raise RuntimeError(
        f"Rollback runtime could not prove prior release {expected_sha}: {last_problem}"
    )


def workflow_url() -> str | None:
    server = os.getenv("GITHUB_SERVER_URL")
    repo = os.getenv("GITHUB_REPOSITORY")
    run_id = os.getenv("GITHUB_RUN_ID")
    if server and repo and run_id:
        return f"{server}/{repo}/actions/runs/{run_id}"
    return None


def write_attestation(
    attestation: ReleaseAttestation,
    path: str = "release-attestation.json",
) -> None:
    payload = json.dumps(asdict(attestation), indent=2, sort_keys=True) + "\n"
    Path(path).write_text(payload, encoding="utf-8")
    print(payload)

    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as handle:
            handle.write("## FAP-Core production release attestation\n\n")
            handle.write(f"- Result: **{attestation.result}**\n")
            handle.write(f"- Git SHA: `{attestation.release_sha}`\n")
            handle.write(f"- Render service: `{attestation.render_service_id}`\n")
            handle.write(f"- Render deploy: `{attestation.render_deploy_id}`\n")
            handle.write(f"- Render SHA: `{attestation.render_deploy_sha}`\n")
            handle.write(f"- Render status: `{attestation.render_status}`\n")
            if attestation.failure:
                handle.write(f"- Failure: `{attestation.failure}`\n")
            if attestation.rollback_deploy_id:
                handle.write(f"- Rollback deploy: `{attestation.rollback_deploy_id}`\n")
                handle.write(f"- Rollback status: `{attestation.rollback_status}`\n")


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


def release() -> ReleaseAttestation:
    token = require_env("RENDER_API_KEY")
    fap_api_key = require_env("FAP_API_KEY")
    release_sha = require_env("RELEASE_SHA")
    service_id = os.getenv("RENDER_SERVICE_ID", DEFAULT_SERVICE_ID).strip()
    health_url = os.getenv("PRODUCTION_HEALTH_URL", DEFAULT_HEALTH_URL).strip()
    identity_url = os.getenv("PRODUCTION_IDENTITY_URL", DEFAULT_IDENTITY_URL).strip()
    api = RenderAPI(token, service_id)

    previous = api.current_live_deploy()
    previous_id = previous.get("id") if previous else None
    previous_sha = deploy_commit_sha(previous)
    rollback_id: str | None = None
    rollback_status: str | None = None
    deployment_started = False

    attestation = ReleaseAttestation(
        schema_version="fap-core.production-release-attestation/1.1",
        release_sha=release_sha,
        expected_repo_slug=EXPECTED_REPO_SLUG,
        expected_branch=EXPECTED_BRANCH,
        expected_service=EXPECTED_SERVICE,
        expected_version=EXPECTED_VERSION,
        render_service_id=service_id,
        previous_live_deploy_id=previous_id,
        previous_live_sha=previous_sha,
        render_deploy_id=None,
        render_deploy_sha=None,
        render_status=None,
        runtime_health=None,
        workflow_url=workflow_url(),
        verified_at=datetime.now(timezone.utc).isoformat(),
        result="started",
    )

    try:
        service = api.get_service()
        if service.get("id") != service_id:
            raise RuntimeError(
                f"Render service identity is {service.get('id')!r}, expected {service_id!r}"
            )
        if service.get("branch") != EXPECTED_BRANCH:
            raise RuntimeError(
                f"Render service branch is {service.get('branch')!r}, expected {EXPECTED_BRANCH!r}"
            )
        repo = str(service.get("repo", "")).rstrip("/")
        if not repo.endswith(f"/{EXPECTED_REPO_SLUG}"):
            raise RuntimeError(f"Unexpected Render repository binding: {repo!r}")

        # GitHub Actions becomes the sole deployment authority. Do not infer that
        # the provider webhook is disabled from the PATCH response: re-read the
        # control plane and require explicit state before any deploy is created.
        api.disable_autodeploy()
        disabled_service = api.get_service()
        if disabled_service.get("autoDeploy") != "no":
            raise RuntimeError(
                f"Render autoDeploy is {disabled_service.get('autoDeploy')!r}, expected 'no'"
            )

        created = api.trigger_deploy(release_sha)
        deploy_id = created.get("id")
        if not deploy_id:
            raise RuntimeError(f"Render did not return a deploy id: {created}")
        deployment_started = True
        attestation.render_deploy_id = deploy_id

        created_sha = deploy_commit_sha(created)
        if created_sha and created_sha != release_sha:
            raise RuntimeError(
                f"Render created deploy for {created_sha}, expected {release_sha}"
            )

        live = wait_for_live(api, deploy_id)
        live_sha = deploy_commit_sha(live)
        attestation.render_deploy_sha = live_sha
        attestation.render_status = str(live.get("status"))
        if live_sha != release_sha:
            raise RuntimeError(
                f"Live Render deploy reports {live_sha}, expected {release_sha}"
            )

        attestation.runtime_health = verify_runtime_health(
            identity_url,
            release_sha,
            service_id,
            fap_api_key,
        )
        attestation.result = "verified"
        attestation.verified_at = datetime.now(timezone.utc).isoformat()
        write_attestation(attestation)
        return attestation

    except Exception as exc:
        attestation.failure = str(exc)
        attestation.result = "failed"
        attestation.verified_at = datetime.now(timezone.utc).isoformat()

        if deployment_started and previous_id and previous_sha and previous_sha != release_sha:
            try:
                rolled = api.rollback(previous_id)
                rollback_id = rolled.get("id")
                if rollback_id:
                    rollback_live = wait_for_live(api, rollback_id)
                    rollback_status = str(rollback_live.get("status"))
                    try:
                        attestation.rollback_runtime_health = verify_rollback_health(
                            health_url,
                            previous_sha,
                            service_id,
                        )
                    except Exception as rollback_health_exc:  # noqa: BLE001
                        rollback_status = (
                            f"{rollback_status}; health-unproven: {rollback_health_exc}"
                        )
                else:
                    rollback_status = "rollback-requested"
            except Exception as rollback_exc:  # noqa: BLE001 - preserve both failures
                rollback_status = f"rollback-failed: {rollback_exc}"

        attestation.rollback_deploy_id = rollback_id
        attestation.rollback_status = rollback_status
        write_attestation(attestation)
        raise


def main() -> int:
    try:
        release()
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"PRODUCTION RELEASE FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
