from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "darkambient"


def test_darkambient_compose_is_private_and_pinned():
    compose = (DEPLOY / "compose.yaml").read_text(encoding="utf-8")
    assert "ghcr.io/docker-mailserver/docker-mailserver:15.1.0" in compose
    assert '"25:25"' in compose
    assert '"127.0.0.1:8012:8010"' in compose
    assert '"587:587"' not in compose
    assert '"993:993"' not in compose
    assert "mx.temp.darkambient.co" in compose


def test_mailserver_config_prevents_docker_open_relay():
    env = (DEPLOY / "mailserver.env").read_text(encoding="utf-8")
    assert "PERMIT_DOCKER=none" in env
    assert "POSTFIX_INET_PROTOCOLS=ipv4" in env
    assert "ENABLE_RSPAMD=1" in env


def test_catch_all_targets_central_mailbox():
    aliases = (DEPLOY / "config-templates" / "postfix-virtual.cf").read_text(encoding="utf-8")
    assert "contact@temp.darkambient.co contact@temp.darkambient.co" in aliases
    assert "@temp.darkambient.co contact@temp.darkambient.co" in aliases


def test_rspamd_dkim_generation_uses_running_rspamd_container():
    runbook = (DEPLOY / "README.md").read_text(encoding="utf-8")
    assert (
        "docker exec darkambient-mailserver "
        "setup config dkim domain temp.darkambient.co"
    ) in runbook
    assert "use_esld = false" in runbook


def test_nginx_routes_only_the_web_app():
    nginx = (DEPLOY / "nginx" / "temp.darkambient.co.conf").read_text(encoding="utf-8")
    assert "server_name temp.darkambient.co;" in nginx
    assert "proxy_pass http://127.0.0.1:8012;" in nginx
    assert "server_name mx.temp.darkambient.co;" in nginx


def test_linux_deploy_artifacts_are_exported_with_lf_endings():
    paths = [
        "deploy/darkambient/compose.yaml",
        "deploy/darkambient/mailserver.env",
        "deploy/darkambient/config-templates/postfix-virtual.cf",
        "deploy/darkambient/nginx/temp.darkambient.co.conf",
        "deploy/darkambient/update.sh",
    ]
    attributes = subprocess.check_output(
        ["git", "check-attr", "eol", "--", *paths],
        cwd=ROOT,
        text=True,
    )
    for path in paths:
        assert f"{path}: eol: lf" in attributes


def test_update_script_fast_forwards_and_checks_health():
    script = (DEPLOY / "update.sh").read_text(encoding="utf-8")

    assert "git diff --quiet" in script
    assert "git fetch origin main" in script
    assert "git merge --ff-only origin/main" in script
    assert "docker compose -f compose.yaml build app" in script
    assert "docker compose -f compose.yaml up -d app" in script
    assert "--retry-all-errors" in script
    assert "https://temp.darkambient.co/api/health" in script
