# Darkambient Temp Mail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy Lush-Temp-Mail at `https://temp.darkambient.co` with catch-all addresses `anything@temp.darkambient.co` and authenticated send/reply/forward through a dedicated mail server on `89.117.21.223`.

**Architecture:** A dedicated Docker Compose project runs the FastAPI app and Docker Mailserver `15.1.0` on one private bridge network. Nginx on the host terminates web TLS and proxies to the app on `127.0.0.1:8012`; only SMTP `25/tcp` is published by the mail container, while app-to-IMAP/SMTP traffic stays internal and authenticated.

**Tech Stack:** Ubuntu 24.04, Docker Engine with Compose V2, Docker Mailserver 15.1.0, Postfix, Dovecot, Rspamd, FastAPI, SQLite, Nginx, Certbot, Cloudflare DNS.

## Global Constraints

- Keep apex `darkambient.co` MX records pointed at Google Workspace.
- Web and temp-mail address domain are both exactly `temp.darkambient.co`.
- Mail exchanger hostname is exactly `mx.temp.darkambient.co`.
- Do not publish app `8010`, IMAP `993`, or submission `587` to the Internet.
- Publish SMTP `25` and preserve SSH/HTTP/HTTPS access.
- Never commit runtime passwords, account hashes, DKIM private keys, TLS private keys, SQLite data, or mailbox data.
- Docker Mailserver image is pinned to `ghcr.io/docker-mailserver/docker-mailserver:15.1.0`.
- Runtime data root on VPS is `/opt/darkambient-temp-mail`.
- Existing Nginx sites and Cloudflare origin certificates must remain intact.

---

## File Structure

- `deploy/darkambient/compose.yaml`: isolated app + mailserver runtime.
- `deploy/darkambient/app.env.example`: secret-free app environment contract.
- `deploy/darkambient/mailserver.env`: non-secret Docker Mailserver settings.
- `deploy/darkambient/config-templates/postfix-virtual.cf`: exact central mailbox and wildcard catch-all mappings.
- `deploy/darkambient/nginx/temp.darkambient.co.conf`: Nginx reverse proxy, login rate limiting, and ACME challenge host.
- `deploy/darkambient/README.md`: deployment, DNS, verification, backup, and rollback runbook.
- `backend/tests/test_darkambient_deploy.py`: static deployment invariants that prevent accidental open ports, wrong domains, unpinned images, or missing catch-all.
- `backend/tests/test_parser.py`: recipient parsing regression for `X-Original-To` at `temp.darkambient.co`.
- `docs/DECISIONS_INDEX.md`: active decision summary for the isolated subdomain mail stack.
- `docs/DECISIONS.md`: canonical decision record with reason and impact.
- `docs/CHANGELOG.md`: one short Project Task entry after verification.

---

### Task 1: Lock deployment invariants with failing tests

**Files:**
- Create: `backend/tests/test_darkambient_deploy.py`
- Modify: `backend/tests/test_parser.py`

**Interfaces:**
- Consumes: repository files addressed from the repo root.
- Produces: pytest assertions for deployment artifacts and recipient extraction.

- [ ] **Step 1: Write the failing deployment artifact test**

```python
from pathlib import Path


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


def test_nginx_routes_only_the_web_app():
    nginx = (DEPLOY / "nginx" / "temp.darkambient.co.conf").read_text(encoding="utf-8")
    assert "server_name temp.darkambient.co;" in nginx
    assert "proxy_pass http://127.0.0.1:8012;" in nginx
    assert "server_name mx.temp.darkambient.co;" in nginx
```

- [ ] **Step 2: Write the parser regression**

```python
def test_extract_recipient_from_darkambient_catch_all_header():
    message = message_from_string(
        "From: sender@example.net\n"
        "To: contact@temp.darkambient.co\n"
        "X-Original-To: launch-742@temp.darkambient.co\n"
        "Subject: verification\n\n"
        "Code 123456"
    )
    assert (
        extract_recipient(message, "temp.darkambient.co", "contact@temp.darkambient.co")
        == "launch-742@temp.darkambient.co"
    )
```

- [ ] **Step 3: Run tests and verify the red state**

Run: `python -m pytest backend/tests/test_darkambient_deploy.py backend/tests/test_parser.py -q`

Expected: deployment tests fail with `FileNotFoundError`; existing parser tests and the new parser regression pass.

---

### Task 2: Add the isolated app and mailserver stack

**Files:**
- Create: `deploy/darkambient/compose.yaml`
- Create: `deploy/darkambient/app.env.example`
- Create: `deploy/darkambient/mailserver.env`
- Create: `deploy/darkambient/config-templates/postfix-virtual.cf`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: root `Dockerfile`, FastAPI env contract, Docker Mailserver FILE provisioner.
- Produces: services `darkambient-temp-app` and `darkambient-mailserver` on network `darkambient_mail`.

- [ ] **Step 1: Create Compose runtime**

```yaml
name: darkambient-temp-mail

services:
  app:
    container_name: darkambient-temp-app
    build:
      context: ../..
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "127.0.0.1:8012:8010"
    volumes:
      - ./data/app:/app/data
    networks:
      - darkambient_mail
    depends_on:
      mailserver:
        condition: service_healthy

  mailserver:
    image: ghcr.io/docker-mailserver/docker-mailserver:15.1.0
    container_name: darkambient-mailserver
    hostname: mx.temp.darkambient.co
    restart: unless-stopped
    env_file:
      - mailserver.env
    ports:
      - "25:25"
    volumes:
      - ./data/mail-data:/var/mail
      - ./data/mail-state:/var/mail-state
      - ./data/mail-logs:/var/log/mail
      - ./data/dms-config:/tmp/docker-mailserver
      - /etc/letsencrypt:/etc/letsencrypt:ro
    cap_add:
      - NET_ADMIN
    stop_grace_period: 1m
    healthcheck:
      test: "ss --listening --tcp | grep -P 'LISTEN.+:smtp' || exit 1"
      interval: 20s
      timeout: 5s
      retries: 6
      start_period: 60s
    networks:
      darkambient_mail:
        aliases:
          - mx.temp.darkambient.co

networks:
  darkambient_mail:
    name: darkambient_mail
```

- [ ] **Step 2: Create secret-free app env contract**

```dotenv
ADMIN_USERNAME=admin
ADMIN_PASSWORD=generated-on-vps
USER_USERNAME=user
USER_PASSWORD=generated-on-vps
SESSION_COOKIE_NAME=darkambient_temp_mail_session
SESSION_TTL_HOURS=168
SECURE_COOKIE=true
APP_BASE_URL=https://temp.darkambient.co
TEMPMAIL_PUBLIC_DOMAIN=temp.darkambient.co
TEMPMAIL_MAIL_DOMAIN=temp.darkambient.co
DEFAULT_ALIAS_HOURS=0
MESSAGE_RETENTION_DAYS=0
IMAP_HOST=mx.temp.darkambient.co
IMAP_PORT=993
IMAP_USERNAME=contact@temp.darkambient.co
IMAP_PASSWORD=generated-on-vps
SMTP_HOST=mx.temp.darkambient.co
SMTP_PORT=587
SMTP_USERNAME=contact@temp.darkambient.co
SMTP_PASSWORD=generated-on-vps
SMTP_SECURITY=starttls
SMTP_FROM_ADDRESS=contact@temp.darkambient.co
SMTP_FROM_NAME=DarkAmbient Temp Mail
CENTRAL_MAILBOX=contact@temp.darkambient.co
MAIL_SYNC_ENABLED=true
MAIL_SYNC_INTERVAL_S=4
MAIL_IDLE_ENABLED=true
MAIL_IDLE_TIMEOUT_S=1500
TEMPMAIL_DATA_DIR=/app/data
TEMPMAIL_DB_PATH=/app/data/darkambient_temp_mail.db
LOG_LEVEL=INFO
```

- [ ] **Step 3: Create Docker Mailserver settings**

```dotenv
OVERRIDE_HOSTNAME=mx.temp.darkambient.co
LOG_LEVEL=info
TZ=Asia/Ho_Chi_Minh
ACCOUNT_PROVISIONER=FILE
PERMIT_DOCKER=none
ENABLE_IMAP=1
ENABLE_POP3=0
ENABLE_CLAMAV=0
ENABLE_RSPAMD=1
ENABLE_RSPAMD_REDIS=1
RSPAMD_GREYLISTING=1
RSPAMD_CHECK_AUTHENTICATED=0
ENABLE_OPENDKIM=0
ENABLE_OPENDMARC=0
ENABLE_POLICYD_SPF=0
ENABLE_AMAVIS=0
ENABLE_SPAMASSASSIN=0
ENABLE_POSTGREY=0
ENABLE_FAIL2BAN=1
FAIL2BAN_BLOCKTYPE=drop
SSL_TYPE=letsencrypt
TLS_LEVEL=modern
SPOOF_PROTECTION=1
POSTFIX_INET_PROTOCOLS=ipv4
DOVECOT_INET_PROTOCOLS=ipv4
MOVE_SPAM_TO_JUNK=1
MARK_SPAM_AS_READ=0
POSTMASTER_ADDRESS=postmaster@temp.darkambient.co
POSTFIX_MESSAGE_SIZE_LIMIT=52428800
ENABLE_QUOTAS=1
```

- [ ] **Step 4: Create the catch-all template**

```text
contact@temp.darkambient.co contact@temp.darkambient.co
postmaster@temp.darkambient.co contact@temp.darkambient.co
abuse@temp.darkambient.co contact@temp.darkambient.co
@temp.darkambient.co contact@temp.darkambient.co
```

- [ ] **Step 5: Ignore runtime secrets and data**

Add:

```gitignore
deploy/darkambient/.env
deploy/darkambient/credentials.txt
deploy/darkambient/data/
```

- [ ] **Step 6: Run deployment tests**

Run: `python -m pytest backend/tests/test_darkambient_deploy.py backend/tests/test_parser.py -q`

Expected: all selected tests pass.

---

### Task 3: Add Nginx and operations runbook

**Files:**
- Create: `deploy/darkambient/nginx/temp.darkambient.co.conf`
- Create: `deploy/darkambient/README.md`

**Interfaces:**
- Consumes: host Nginx, existing wildcard Cloudflare Origin certificate, app loopback port `8012`, Certbot webroot.
- Produces: HTTPS web route and HTTP ACME route for `mx.temp.darkambient.co`.

- [ ] **Step 1: Create Nginx config**

```nginx
limit_req_zone $binary_remote_addr zone=darkambient_login:10m rate=10r/m;

server {
    listen 80;
    listen [::]:80;
    server_name temp.darkambient.co;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name temp.darkambient.co;

    ssl_certificate /etc/ssl/cloudflare/darkambient.co.pem;
    ssl_certificate_key /etc/ssl/cloudflare/darkambient.co.key;

    location = /api/auth/login {
        limit_req zone=darkambient_login burst=5 nodelay;
        proxy_pass http://127.0.0.1:8012;
        include proxy_params;
    }

    location / {
        proxy_pass http://127.0.0.1:8012;
        include proxy_params;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_read_timeout 1800s;
    }
}

server {
    listen 80;
    listen [::]:80;
    server_name mx.temp.darkambient.co;
    root /var/www/letsencrypt;

    location /.well-known/acme-challenge/ {
        try_files $uri =404;
    }

    location / {
        return 204;
    }
}
```

- [ ] **Step 2: Write the runbook with exact DNS records**

Document:

```text
A     temp       89.117.21.223             Proxied
A     mx.temp    89.117.21.223             DNS only
MX    temp       mx.temp.darkambient.co    Priority 10
TXT   temp       v=spf1 mx -all
TXT   _dmarc.temp v=DMARC1; p=none; rua=mailto:postmaster@temp.darkambient.co; adkim=s; aspf=s
TXT   mail._domainkey.temp  value read from the DMS-generated `mail.txt` public record
PTR   89.117.21.223 -> mx.temp.darkambient.co
```

Include backup commands for `/opt/darkambient-temp-mail/app/deploy/darkambient/data`, verification commands, credential rotation, and rollback that disables only the new Compose project and Nginx site.

- [ ] **Step 3: Re-run tests and validate source formatting**

Run:

```powershell
python -m pytest -q
Get-ChildItem .\backend\app\*.py | ForEach-Object { python -m py_compile $_.FullName }
node --check .\app.js
node --check .\user.js
git diff --check
```

Expected: pytest has zero failures; Python/Node syntax commands and `git diff --check` exit `0`.

- [ ] **Step 4: Commit deployment artifacts**

```bash
git add .gitignore backend/tests/test_darkambient_deploy.py backend/tests/test_parser.py deploy/darkambient
git commit -m "feat: add darkambient temp mail deployment"
```

---

### Task 4: Prepare and secure the VPS runtime

**Files:**
- Remote create: `/opt/darkambient-temp-mail/app`
- Remote create: `/opt/darkambient-temp-mail/backups`
- Remote modify: Docker apt repository and packages.

**Interfaces:**
- Consumes: SSH access to `root@89.117.21.223`, committed repository archive.
- Produces: Docker Engine + Compose V2 and a recoverable application checkout.

- [ ] **Step 1: Capture pre-deployment state**

Run remotely:

```bash
stamp="$(date +%Y%m%d%H%M%S)"
mkdir -p "/opt/darkambient-temp-mail/backups/$stamp"
nginx -T > "/opt/darkambient-temp-mail/backups/$stamp/nginx-T.txt" 2>&1
ss -ltnp > "/opt/darkambient-temp-mail/backups/$stamp/listeners.txt"
dpkg-query -W > "/opt/darkambient-temp-mail/backups/$stamp/packages.txt"
cp -a /etc/nginx "/opt/darkambient-temp-mail/backups/$stamp/nginx"
```

Expected: backup directory contains Nginx, listener and package snapshots.

- [ ] **Step 2: Install Docker from its official apt repository**

Run remotely using the Docker Ubuntu 24.04 repository procedure:

```bash
apt-get update
apt-get install -y ca-certificates curl git
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
cat > /etc/apt/sources.list.d/docker.sources <<'EOF'
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Architectures: amd64
Signed-By: /etc/apt/keyrings/docker.asc
EOF
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
docker version
docker compose version
```

Expected: Docker server and Compose V2 versions print successfully.

- [ ] **Step 3: Transfer a clean Git archive**

Create locally:

```powershell
git archive --format=tar.gz -o darkambient-temp-mail.tar.gz HEAD
```

Copy to `/opt/darkambient-temp-mail/`, verify the absolute target, extract into `/opt/darkambient-temp-mail/app`, then remove only the transferred archive.

- [ ] **Step 4: Validate Compose before creating services**

Run remotely:

```bash
cd /opt/darkambient-temp-mail/app/deploy/darkambient
cp app.env.example .env
docker compose -f compose.yaml config --quiet
```

Expected: exit `0` with no interpolation or schema errors.

---

### Task 5: Provision credentials, mailbox, catch-all and DKIM

**Files:**
- Remote create: `deploy/darkambient/.env` mode `600`.
- Remote create: `deploy/darkambient/credentials.txt` mode `600`.
- Remote create: `deploy/darkambient/data/dms-config/postfix-accounts.cf`.
- Remote create: `deploy/darkambient/data/dms-config/postfix-virtual.cf`.
- Remote create: DKIM files under `deploy/darkambient/data/dms-config/rspamd/`.

**Interfaces:**
- Consumes: OpenSSL random generator and DMS `setup` CLI.
- Produces: app/admin/user/mail credentials and a functional central mailbox.

- [ ] **Step 1: Generate four independent secrets without printing them**

Run remotely:

```bash
cd /opt/darkambient-temp-mail/app/deploy/darkambient
umask 077
admin_password="$(openssl rand -base64 24 | tr -d '\n')"
user_password="$(openssl rand -base64 24 | tr -d '\n')"
mail_password="$(openssl rand -base64 32 | tr -d '\n')"
cp app.env.example .env
sed -i "s|ADMIN_PASSWORD=generated-on-vps|ADMIN_PASSWORD=$admin_password|" .env
sed -i "s|USER_PASSWORD=generated-on-vps|USER_PASSWORD=$user_password|" .env
sed -i "s|IMAP_PASSWORD=generated-on-vps|IMAP_PASSWORD=$mail_password|" .env
sed -i "s|SMTP_PASSWORD=generated-on-vps|SMTP_PASSWORD=$mail_password|" .env
printf 'ADMIN_USERNAME=admin\nADMIN_PASSWORD=%s\nUSER_USERNAME=user\nUSER_PASSWORD=%s\nMAIL_USERNAME=contact@temp.darkambient.co\nMAIL_PASSWORD=%s\n' \
  "$admin_password" "$user_password" "$mail_password" > credentials.txt
chmod 600 .env credentials.txt
unset admin_password user_password mail_password
```

Expected: `.env` and `credentials.txt` are mode `600`; secrets are not emitted to terminal output.

- [ ] **Step 2: Provision the central mailbox with the stored password**

Run remotely:

```bash
cd /opt/darkambient-temp-mail/app/deploy/darkambient
mkdir -p data/dms-config data/mail-data data/mail-state data/mail-logs data/app
mail_password="$(sed -n 's/^MAIL_PASSWORD=//p' credentials.txt)"
docker run --rm \
  -v "$PWD/data/dms-config:/tmp/docker-mailserver" \
  ghcr.io/docker-mailserver/docker-mailserver:15.1.0 \
  setup email add contact@temp.darkambient.co "$mail_password"
unset mail_password
cp config-templates/postfix-virtual.cf data/dms-config/postfix-virtual.cf
chmod 600 data/dms-config/postfix-accounts.cf
```

Expected: account hash exists; plaintext mail password exists only in `.env` and `credentials.txt`.

- [ ] **Step 3: Generate DKIM for the exact sender domain**

Run remotely:

```bash
docker exec darkambient-mailserver \
  setup config dkim domain temp.darkambient.co
sed -i 's/use_esld = true;/use_esld = false;/' \
  data/dms-config/rspamd/override.d/dkim_signing.conf
docker exec darkambient-mailserver supervisorctl restart rspamd
find data/dms-config/rspamd/dkim -maxdepth 1 -type f -ls
```

Expected: a private key and public DNS record for selector `mail` are present; only public record content may be copied to DNS.

---

### Task 6: Apply DNS, TLS, Nginx and start services

**Files:**
- Remote create: `/etc/nginx/sites-available/temp.darkambient.co.conf`.
- Remote create: `/etc/nginx/sites-enabled/temp.darkambient.co.conf` symlink.
- Remote create: `/etc/letsencrypt/live/mx.temp.darkambient.co/` via Certbot.

**Interfaces:**
- Consumes: Cloudflare access, generated DKIM public record, existing wildcard Cloudflare Origin certificate.
- Produces: public DNS, mail TLS, HTTPS web route, running containers.

- [ ] **Step 1: Apply DNS without altering apex MX**

Create/update exactly the records in Task 3. Before and after the change, save:

```powershell
Resolve-DnsName darkambient.co -Type MX
Resolve-DnsName temp.darkambient.co -Type A
Resolve-DnsName temp.darkambient.co -Type MX
Resolve-DnsName mx.temp.darkambient.co -Type A
```

Expected: apex MX remains Google; `temp` and `mx.temp` resolve to the new values.

- [ ] **Step 2: Install and validate Nginx site**

Run remotely:

```bash
mkdir -p /var/www/letsencrypt
cp /opt/darkambient-temp-mail/app/deploy/darkambient/nginx/temp.darkambient.co.conf /etc/nginx/sites-available/temp.darkambient.co.conf
ln -sfn /etc/nginx/sites-available/temp.darkambient.co.conf /etc/nginx/sites-enabled/temp.darkambient.co.conf
nginx -t
systemctl reload nginx
```

Expected: `nginx -t` reports successful syntax and reload exits `0`.

- [ ] **Step 3: Issue the public certificate for the mail hostname**

Run remotely after `mx.temp.darkambient.co` resolves to the VPS:

```bash
certbot certonly --webroot \
  --webroot-path /var/www/letsencrypt \
  --domain mx.temp.darkambient.co \
  --non-interactive --agree-tos --register-unsafely-without-email
certbot certificates
```

Expected: a valid certificate exists at `/etc/letsencrypt/live/mx.temp.darkambient.co/fullchain.pem`.

- [ ] **Step 4: Start the stack**

Run remotely:

```bash
cd /opt/darkambient-temp-mail/app/deploy/darkambient
docker compose -f compose.yaml pull mailserver
docker compose -f compose.yaml up -d --build
docker compose -f compose.yaml ps
docker logs --tail 100 darkambient-mailserver
docker logs --tail 100 darkambient-temp-app
```

Expected: both services are running; mailserver becomes healthy; app health endpoint succeeds internally.

- [ ] **Step 5: Add host firewall rules without relying on UFW for Docker filtering**

Run remotely:

```bash
apt-get install -y ufw
ufw allow 22/tcp
ufw allow 25/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
ufw status verbose
```

Expected: SSH remains connected and the four required public ports are allowed. Confirm separately that only `25` is published by Docker.

---

### Task 7: End-to-end verification and handoff

**Files:**
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/DECISIONS_INDEX.md`
- Modify: `docs/DECISIONS.md`
- Remote retain: `/opt/darkambient-temp-mail/app/deploy/darkambient/credentials.txt` mode `600`.

**Interfaces:**
- Consumes: deployed DNS, app, SMTP, IMAP, generated credentials.
- Produces: fresh evidence for functionality, security and rollback readiness.

- [ ] **Step 1: Verify DNS isolation**

Run:

```powershell
Resolve-DnsName darkambient.co -Type MX
Resolve-DnsName temp.darkambient.co -Type MX
Resolve-DnsName temp.darkambient.co -Type TXT
Resolve-DnsName mail._domainkey.temp.darkambient.co -Type TXT
Resolve-DnsName _dmarc.temp.darkambient.co -Type TXT
Resolve-DnsName 223.21.117.89.in-addr.arpa -Type PTR
```

Expected: apex MX is unchanged; subdomain MX/SPF/DKIM/DMARC are published; PTR is `mx.temp.darkambient.co` after provider-side update.

- [ ] **Step 2: Verify public and private ports**

Run local TCP checks against `89.117.21.223` for `22,25,80,443,587,993,8012`.

Expected: `22,25,80,443` open; `587,993,8012` closed publicly.

- [ ] **Step 3: Verify app health, HTTPS and role login**

Run remotely:

```bash
docker exec darkambient-temp-app python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8010/api/health', timeout=10).read().decode())"
curl -fsS https://temp.darkambient.co/api/health
```

Then authenticate once with admin and user credentials and confirm role routing.

Expected: health returns success; admin reaches `/`, user reaches `/user.html`.

- [ ] **Step 4: Verify catch-all receive and parser path**

Send an SMTP message from outside the container to a random address at `temp.darkambient.co`. Confirm Postfix accepts it, Dovecot stores it, IMAP sync imports it, and the app displays the random alias with correct subject/body/OTP/link.

Expected: no alias pre-creation is required.

- [ ] **Step 5: Verify send, reply and forward**

Use the admin UI to send a new message, reply to the received test message and forward it with an attachment. Inspect the recipient headers.

Expected: all three arrive; DKIM, SPF and DMARC report pass or aligned pass where the receiving provider exposes authentication results.

- [ ] **Step 6: Verify relay is closed**

Attempt an unauthenticated SMTP transaction from outside with a non-local sender and non-local recipient.

Expected: Postfix rejects relay with `Relay access denied` or equivalent `5xx`; it must not queue the message.

- [ ] **Step 7: Record the active architecture decision and changelog entry**

Append `DEC-004` to `docs/DECISIONS_INDEX.md`: use a dedicated Docker Mailserver for `temp.darkambient.co` on `89.117.21.223`, while preserving Google Workspace for apex `darkambient.co`.

Append one canonical row to `docs/DECISIONS.md` with the reason (mail isolation and rollback safety), impact (new DNS/MX/PTR and Docker runtime only under the subdomain), and date `2026-07-21`.

Append one `docs/CHANGELOG.md` entry describing the dedicated Darkambient deployment artifacts and verified VPS deployment.

- [ ] **Step 8: Run final local verification**

Run:

```powershell
python -m pytest -q
Get-ChildItem .\backend\app\*.py | ForEach-Object { python -m py_compile $_.FullName }
node --check .\app.js
node --check .\user.js
git diff --check
```

Expected: zero failures and exit `0` for every command.

- [ ] **Step 9: Commit final documentation**

```bash
git add docs/CHANGELOG.md docs/DECISIONS.md docs/DECISIONS_INDEX.md
git commit -m "docs: record darkambient mail deployment"
```

- [ ] **Step 10: Handoff credentials and provider-only action**

Return the web URL, admin/user credentials, DKIM/SPF/DMARC status, and evidence summary. If PTR cannot be changed from the VPS, clearly identify the single provider action: set `89.117.21.223` PTR to `mx.temp.darkambient.co`.
