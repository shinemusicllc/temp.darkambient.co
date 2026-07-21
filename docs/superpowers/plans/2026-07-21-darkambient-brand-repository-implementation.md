# DarkAmbient Branding and Independent Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebrand the live app as DarkAmbient, publish a secret-free public repository named `temp.darkambient.co` with a clean history, and make local and VPS checkouts track its `main` branch.

**Architecture:** Keep the FastAPI and vanilla HTML/CSS/JS application unchanged except for code-native branding assets and copy. Produce the public repository from a tracked-file archive so no previous Git history or ignored runtime state can enter it, then replace the live source directory with a verified clone while restoring only ignored production state.

**Tech Stack:** FastAPI, pytest, vanilla HTML/CSS/JavaScript, SVG, Git/GitHub, Docker Compose, Nginx, PowerShell, Bash

## Global Constraints

- The repository is public and named exactly `temp.darkambient.co`.
- The new repository starts with one clean initial commit and has only the operational remote `origin`.
- The canonical local checkout is `C:\Users\Cong-PC\Desktop\temp.darkambient.co` on `main` tracking `origin/main`.
- The VPS checkout is `/opt/darkambient-temp-mail/app` on `main` tracking `origin/main`.
- Never publish `.env`, credentials, SQLite databases, mailbox data, DKIM/TLS private keys, certificates, backups, archives, caches, or worktrees.
- Preserve the current layout, typography, orange accent, spacing, responsive behavior, mail flow, DNS, and Google Workspace apex MX records.
- Preserve Vietnamese source text as UTF-8.

---

### Task 1: DarkAmbient brand surfaces

**Files:**
- Create: `backend/tests/test_branding.py`
- Modify: `logo.svg`
- Modify: `index.html`
- Modify: `user.html`
- Modify: `app.js`
- Modify: `backend/app/config.py`
- Modify: `backend/app/translator.py`
- Modify: `deploy/darkambient/app.env.example`

**Interfaces:**
- Consumes: existing `logo.svg` references and the `lush-*` color tokens already defined in both HTML entrypoints.
- Produces: accessible `DA` SVG mark, visible `DarkAmbient` wordmarks, DarkAmbient metadata, and `DarkAmbient` sender fallbacks.

- [ ] **Step 1: Write the failing branding tests**

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_active_surfaces_use_darkambient_brand():
    index_html = read("index.html")
    user_html = read("user.html")
    app_js = read("app.js")

    assert "DarkAmbient Admin" in index_html
    assert "DarkAmbient Inbox" in user_html
    assert "Dark<span class=\"text-lush-500\">Ambient</span>" in index_html
    assert "DarkAmbient" in user_html
    assert "logo.svg?v=20260721-darkambient-brand" in index_html
    assert "logo.svg?v=20260721-darkambient-brand" in user_html
    assert "from_email || 'DarkAmbient'" in app_js
    assert "LushMail" not in index_html
    assert "LushMail" not in user_html
    assert "from_email || 'LushMail'" not in app_js


def test_logo_is_accessible_darkambient_monogram():
    logo = read("logo.svg")
    assert "DarkAmbient Logo" in logo
    assert "DA monogram" in logo
    assert '#ff5528' in logo
```

- [ ] **Step 2: Run the branding tests and verify RED**

Run: `python -m pytest backend/tests/test_branding.py -q`  
Expected: FAIL because active surfaces and SVG still contain `LushMail`/`Lush Media`.

- [ ] **Step 3: Replace the SVG mark and active brand copy**

Implement a compact `DA` monogram in `logo.svg` with the existing `viewBox="0 0 256 256"` and `#ff5528` fill. Use `<title id="title">DarkAmbient Logo</title>` and `<desc id="desc">Stylized DA monogram in orange</desc>`.

Update both page titles/descriptions, all logo alt text, wordmarks, and logo/favicons to use `logo.svg?v=20260721-darkambient-brand` so browsers cannot reuse the old mark. Replace stale `lushmedia.net` UI examples with `temp.darkambient.co`. In the admin wordmark preserve the existing split styling:

```html
<span class="font-fustat font-bold text-xl text-gray-900">Dark<span class="text-lush-500">Ambient</span></span>
```

On the dark user hero, keep the existing white wordmark treatment and change only the text to `DarkAmbient`. Change both `app.js` sender fallbacks, the backend `SMTP_FROM_NAME` default, the translator `User-Agent`, and the DarkAmbient environment template to `DarkAmbient`.

- [ ] **Step 4: Run the branding tests and verify GREEN**

Run: `python -m pytest backend/tests/test_branding.py -q`  
Expected: `2 passed`.

- [ ] **Step 5: Commit the branding change**

```bash
git add backend/tests/test_branding.py logo.svg index.html user.html app.js backend/app/config.py backend/app/translator.py deploy/darkambient/app.env.example
git commit -m "feat: rebrand app as DarkAmbient"
```

### Task 2: Git-based VPS update workflow

**Files:**
- Create: `deploy/darkambient/update.sh`
- Modify: `backend/tests/test_darkambient_deploy.py`
- Modify: `deploy/darkambient/README.md`
- Modify: `.gitattributes`

**Interfaces:**
- Consumes: checkout at `/opt/darkambient-temp-mail/app`, remote `origin/main`, Compose file `deploy/darkambient/compose.yaml`, and health endpoint `/api/health`.
- Produces: executable `update.sh` that permits only a clean fast-forward update, rebuilds the app, and fails when health verification fails.

- [ ] **Step 1: Add a failing deployment workflow test**

Append a test that reads `deploy/darkambient/update.sh` and asserts these contracts:

```python
def test_update_script_fast_forwards_and_checks_health():
    script = (ROOT / "deploy/darkambient/update.sh").read_text(encoding="utf-8")
    assert "git diff --quiet" in script
    assert "git fetch origin main" in script
    assert "git merge --ff-only origin/main" in script
    assert "docker compose -f compose.yaml build app" in script
    assert "docker compose -f compose.yaml up -d app" in script
    assert "https://temp.darkambient.co/api/health" in script
```

- [ ] **Step 2: Run the deployment test and verify RED**

Run: `python -m pytest backend/tests/test_darkambient_deploy.py -q`  
Expected: FAIL because `deploy/darkambient/update.sh` does not exist.

- [ ] **Step 3: Implement the update script**

Create an LF-terminated executable script with this control flow:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/darkambient-temp-mail/app}"
cd "$APP_DIR"
git diff --quiet
git diff --cached --quiet
git fetch origin main
git merge --ff-only origin/main

cd deploy/darkambient
docker compose -f compose.yaml config --quiet
docker compose -f compose.yaml build app
docker compose -f compose.yaml up -d app
curl --fail --silent --show-error --retry 12 --retry-delay 2 \
  https://temp.darkambient.co/api/health
docker compose -f compose.yaml ps
```

Document the local push and VPS update commands in `deploy/darkambient/README.md`. Add `deploy/darkambient/*.sh text eol=lf` to `.gitattributes`.

- [ ] **Step 4: Verify the deployment workflow**

Run: `python -m pytest backend/tests/test_darkambient_deploy.py -q`  
Expected: all tests in the file PASS.

Run: `bash -n deploy/darkambient/update.sh` when Bash is available; otherwise validate with the script contract test and run `bash -n` on the VPS before activating it.

- [ ] **Step 5: Commit the update workflow**

```bash
git add .gitattributes deploy/darkambient/update.sh deploy/darkambient/README.md backend/tests/test_darkambient_deploy.py
git commit -m "feat: add Git-based VPS updates"
```

### Task 3: Project memory and source verification

**Files:**
- Modify: `docs/PROJECT_BRIEF.md`
- Modify: `docs/UI_SYSTEM.md`
- Modify: `docs/MEMORY_INDEX.md`
- Modify: `docs/DECISIONS_INDEX.md`
- Modify: `docs/DECISIONS.md`
- Modify: `docs/CHANGELOG.md`

**Interfaces:**
- Consumes: final brand and repository/deployment decisions.
- Produces: canonical memory that identifies DarkAmbient and routes future maintenance to the new deployment runbook.

- [ ] **Step 1: Update canonical memory**

Change current product references from LushMail to DarkAmbient in `PROJECT_BRIEF.md` and `UI_SYSTEM.md`. Add one active decision recording the clean independent public repository and Git-tracked VPS checkout. Add one concise changelog entry covering branding and maintenance workflow; do not rewrite historical logs.

- [ ] **Step 2: Run full source verification**

```powershell
python -m pytest backend/tests -q
python -m compileall -q backend
& 'C:\Users\Cong-PC\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --check app.js
& 'C:\Users\Cong-PC\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --check user.js
git diff --check
```

Expected: all tests pass, both syntax checks exit `0`, and `git diff --check` prints no errors.

- [ ] **Step 3: Commit memory updates**

```bash
git add docs/PROJECT_BRIEF.md docs/UI_SYSTEM.md docs/MEMORY_INDEX.md docs/DECISIONS_INDEX.md docs/DECISIONS.md docs/CHANGELOG.md
git commit -m "docs: record DarkAmbient maintenance model"
```

### Task 4: Clean public repository and canonical local checkout

**Files:**
- Create directory: `C:\Users\Cong-PC\Desktop\temp.darkambient.co`
- Create transient archive outside the checkout and remove it after extraction.

**Interfaces:**
- Consumes: committed tracked snapshot from the implementation worktree.
- Produces: a new Git repository with one initial commit on `main`, public GitHub `origin`, and a clean local checkout.

- [ ] **Step 1: Verify the target and export tracked files only**

Confirm the resolved target is exactly `C:\Users\Cong-PC\Desktop\temp.darkambient.co`. Stop if it already contains user files. Export `HEAD` with `git archive`, extract it into the target, and confirm `.git`, `.env`, `credentials.txt`, `data`, and backup archives are absent.

- [ ] **Step 2: Initialize the clean history**

```powershell
git -C 'C:\Users\Cong-PC\Desktop\temp.darkambient.co' init -b main
git -C 'C:\Users\Cong-PC\Desktop\temp.darkambient.co' add -A
git -C 'C:\Users\Cong-PC\Desktop\temp.darkambient.co' commit -m "Initial DarkAmbient temp mail server"
```

Expected: `git rev-list --count HEAD` prints `1`.

- [ ] **Step 3: Scan the staged snapshot and commit for secrets**

List tracked files and reject runtime patterns. Search tracked content for private-key headers, password assignments, tokens, the supplied VPS password, and other likely secrets. Explicitly allow only safe placeholders in `.env.example`.

Expected: no private key, credential handoff, runtime database, or real secret is tracked.

- [ ] **Step 4: Create and push the public repository**

Create `temp.darkambient.co` in the authenticated GitHub account, set it public, add it as `origin`, and push `main`. Prefer the installed GitHub connector when it supports repository creation; otherwise use authenticated GitHub CLI:

```powershell
gh repo create temp.darkambient.co --public --source 'C:\Users\Cong-PC\Desktop\temp.darkambient.co' --remote origin --push
```

- [ ] **Step 5: Verify GitHub and local tracking**

Expected checks:

```powershell
git -C 'C:\Users\Cong-PC\Desktop\temp.darkambient.co' status -sb
git -C 'C:\Users\Cong-PC\Desktop\temp.darkambient.co' remote -v
git -C 'C:\Users\Cong-PC\Desktop\temp.darkambient.co' rev-list --count HEAD
```

The branch must show `main...origin/main`, only `origin` may exist, the worktree must be clean, and commit count must be `1`.

### Task 5: Convert the live VPS to the new checkout

**Files:**
- Replace checkout: `/opt/darkambient-temp-mail/app`
- Preserve runtime: `/opt/darkambient-temp-mail/app/deploy/darkambient/.env`
- Preserve runtime: `/opt/darkambient-temp-mail/app/deploy/darkambient/credentials.txt`
- Preserve runtime: `/opt/darkambient-temp-mail/app/deploy/darkambient/data`

**Interfaces:**
- Consumes: public `origin/main`, current live runtime state, and the verified `update.sh`.
- Produces: clean VPS checkout tracking `origin/main` with healthy production containers.

- [ ] **Step 1: Create a VPS source/runtime backup**

Resolve all paths under `/opt/darkambient-temp-mail`, create a timestamped backup directory, and archive current source plus runtime state before any directory swap. Record SHA-256 hashes for backup archives.

- [ ] **Step 2: Prepare the new clone beside the live directory**

Clone `origin/main` to `/opt/darkambient-temp-mail/app.next`, verify branch/remote/status, and run a tracked-file secret check. Copy only `.env`, retained `credentials.txt`, and `data` from the live directory into their ignored paths in `app.next`; set secret files to mode `600`.

- [ ] **Step 3: Validate before the swap**

Run:

```bash
bash -n /opt/darkambient-temp-mail/app.next/deploy/darkambient/update.sh
cd /opt/darkambient-temp-mail/app.next/deploy/darkambient
docker compose -f compose.yaml config --quiet
```

Expected: both commands exit `0`.

- [ ] **Step 4: Swap checkout and redeploy**

Rename current `app` to a timestamped rollback directory, rename `app.next` to `app`, then build/recreate the app using the new checkout. Keep the existing mailserver data and container configuration.

- [ ] **Step 5: Verify live production and checkout tracking**

Verify:

- `docker compose ps` reports the mailserver healthy and the app running;
- local and public `/api/health` return status `ok`;
- public HTML contains `DarkAmbient` and the new asset version;
- `logo.svg` contains the accessible `DA` monogram;
- `/opt/darkambient-temp-mail/app` is clean on `main...origin/main`;
- the app image does not contain `.env`, `credentials.txt`, or deployment data;
- Google Workspace apex MX and the `temp.darkambient.co` MX/SPF/DKIM/DMARC records remain unchanged.

- [ ] **Step 6: Keep rollback and document its path**

Do not delete the previous source directory. Report the exact rollback path and the one-command update workflow to the user.

### Task 6: Final end-to-end verification and handoff

**Files:**
- Modify if verification changes knowledge: `docs/CHANGELOG.md`

**Interfaces:**
- Consumes: GitHub repository, local checkout, and live VPS checkout.
- Produces: evidence-backed completion report and maintenance handoff.

- [ ] **Step 1: Re-run the full local suite from the canonical checkout**

Run the Task 3 verification commands from `C:\Users\Cong-PC\Desktop\temp.darkambient.co` and require a clean worktree.

- [ ] **Step 2: Verify repository visibility and history**

Confirm the GitHub URL is public, `main` is the default branch, and the new repository has one clean initial commit at publication time.

- [ ] **Step 3: Verify live branding visually**

Reload `https://temp.darkambient.co/`, inspect the admin login/header and user brand surface, and confirm the new mark/wordmark retain the established spacing and do not introduce overflow or layout shifts.

- [ ] **Step 4: Report the maintenance workflow**

Provide the GitHub URL, local checkout, VPS checkout, update command, rollback directory, verification results, and any external deliverability follow-up that remains.
