from pathlib import Path

DOCKERFILE = Path("Dockerfile")
RUNTIME = Path("runtime.txt")
RUNTIME_REQUIREMENTS = Path("requirements.txt")
DEV_REQUIREMENTS = Path("requirements-dev.txt")
SETUP = Path("setup.py")
TESTS_WORKFLOW = Path(".github/workflows/tests.yml")


def test_python_runtime_family_is_aligned():
    assert "FROM python:3.12.11-slim" in DOCKERFILE.read_text(encoding="utf-8")
    assert RUNTIME.read_text(encoding="utf-8").strip() == "python-3.12.11"

    setup = SETUP.read_text(encoding="utf-8")
    assert 'python_requires=">=3.12,<3.14"' in setup


def test_runtime_dependencies_are_exact_and_test_tools_are_not_runtime_dependencies():
    runtime = RUNTIME_REQUIREMENTS.read_text(encoding="utf-8")
    dev = DEV_REQUIREMENTS.read_text(encoding="utf-8")

    assert "requests==2.31.0" in runtime
    assert "requests>=" not in runtime
    assert "pytest" not in runtime
    assert "pytest==8.3.0" in dev


def test_ci_runner_python_and_actions_are_fixed():
    text = TESTS_WORKFLOW.read_text(encoding="utf-8")

    assert "runs-on: ubuntu-24.04" in text
    assert 'python-version: ["3.12.14", "3.13.15"]' in text
    assert "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803" in text
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97" in text
    assert '"pip==26.2.1"' in text
