from pathlib import Path

RELEASE = Path(".github/workflows/release-production.yml")
GREETINGS = Path(".github/workflows/greetings.yml")


def test_release_actions_are_immutable_node24_generation():
    text = RELEASE.read_text(encoding="utf-8")

    assert "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803" in text
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97" in text
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in text
    assert "actions/checkout@v" not in text
    assert "actions/upload-artifact@v" not in text


def test_release_permissions_are_least_privilege():
    text = RELEASE.read_text(encoding="utf-8")

    assert "contents: read" in text
    assert "actions: read" in text
    assert "pull-requests: read" in text
    assert "deployments: write" not in text


def test_untrusted_pull_request_target_greeting_workflow_is_absent():
    assert not GREETINGS.exists()
