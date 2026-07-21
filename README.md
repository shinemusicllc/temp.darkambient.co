# DarkAmbient Temp Mail

DarkAmbient is a FastAPI and vanilla HTML/CSS/JavaScript temp-mail application for `@temp.darkambient.co`. It provides catch-all inbox discovery, OTP/link extraction, message reading, standalone sending, reply, forward, user/admin sessions, and a dedicated Docker Mailserver runtime.

## Production

- Web UI: `https://temp.darkambient.co`
- Catch-all addresses: `anything@temp.darkambient.co`
- Mail hostname: `mx.temp.darkambient.co`
- Apex `darkambient.co` mail remains on Google Workspace.

## Local verification

```powershell
python -m pytest backend/tests -q
python -m compileall -q backend
node --check app.js
node --check user.js
```

Run the development server from the repository root:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8010 --reload
```

## Deployment

Production configuration and the maintenance workflow are documented in [`deploy/darkambient/README.md`](deploy/darkambient/README.md). The VPS checkout tracks `origin/main`; a normal update is:

```bash
cd /opt/darkambient-temp-mail/app
sudo bash deploy/darkambient/update.sh
```

Runtime `.env`, credentials, databases, mailbox data, DKIM/TLS private keys, and backups must never be committed.
