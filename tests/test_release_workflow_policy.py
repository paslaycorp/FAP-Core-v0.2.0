from pathlib import Path

WORKFLOW = Path(".github/workflows/release-production.yml")


def test_production_release_requires_explicit_manual_dispatch():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "workflow_run:" not in text
    assert 'required: true' in text
    assert 'description: "Exact merged main-branch commit SHA to release"' in text


def test_production_release_actions_are_immutable_and_runner_is_fixed():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "runs-on: ubuntu-24.04" in text
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in text
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97" in text
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in text
    assert "actions/checkout@v" not in text
    assert "actions/setup-python@v" not in text
    assert "actions/upload-artifact@v" not in text


def test_release_dependencies_are_exactly_pinned():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert '"requests==2.31.0"' in text
    assert '"pytest==8.3.0"' in text
    assert "requests>=" not in text
    assert "pytest>=" not in text


def test_release_requires_merge_commit_topology_and_exact_python():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "Require merge-commit topology" in text
    assert 'if [[ "${#parts[@]}" -ne 3 ]]' in text
    assert 'python-version: "3.12.14"' in text
