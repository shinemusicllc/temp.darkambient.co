from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_docker_context_excludes_darkambient_runtime_secrets_and_data():
    dockerignore_path = ROOT / ".dockerignore"
    assert dockerignore_path.exists(), ".dockerignore is required for safe production builds"

    patterns = {
        line.strip()
        for line in dockerignore_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert "deploy/darkambient/.env" in patterns
    assert "deploy/darkambient/credentials.txt" in patterns
    assert "deploy/darkambient/data/" in patterns
