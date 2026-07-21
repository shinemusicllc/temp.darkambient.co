# DarkAmbient Branding and Independent Repository Design

**Date:** 2026-07-21  
**Status:** Approved for planning  
**Scope:** Product branding, independent GitHub repository, local checkout, and VPS Git-based deployment

## Goal

Replace the remaining LushMail identity with DarkAmbient while preserving the existing mail-workspace visual language. Publish the application as a new public GitHub repository named `temp.darkambient.co` with a clean Git history, then make both the local maintenance copy and the VPS deployment track that repository's `main` branch.

## Branding

- Replace `logo.svg` with a code-native SVG monogram using the letters `DA`.
- Keep the current orange brand color and the compact proportions of the existing mark so the navigation, login card, favicon, and user header do not require layout changes.
- Render the wordmark as `DarkAmbient`, with `Dark` in the existing slate text color and `Ambient` in the existing orange accent.
- Update admin and user page titles, descriptions, image alternative text, visible wordmarks, and sender fallbacks.
- Do not redesign navigation, spacing, typography, buttons, mail rows, panels, or responsive behavior.
- Preserve all Vietnamese UI strings as UTF-8.

## Repository Model

- Create a new public GitHub repository named `temp.darkambient.co`.
- Start the repository from one clean initial commit; do not copy the current repository's Git history.
- The new repository has one operational remote named `origin` and no `upstream` link to the reference repository.
- Create the canonical local checkout at `C:\Users\Cong-PC\Desktop\temp.darkambient.co`.
- Use `main` as the default branch and track `origin/main`.
- The current worktree remains a temporary build source only; future maintenance happens in the new canonical checkout.

## Public Repository Safety

Before the initial commit, verify that the snapshot excludes:

- `.env` and environment overrides;
- generated credentials and password handoff files;
- SQLite databases, mailbox data, DKIM private keys, TLS private keys, and certificates;
- deployment backups, transfer archives, caches, and local worktrees;
- host-specific runtime state.

Keep safe templates, Docker Compose definitions, deployment scripts, and the operating runbook in the public repository. Scan both tracked files and the final initial commit for likely secrets before pushing.

## VPS Checkout and Deployment

- Create a fresh source backup before changing the live checkout.
- Prepare a new clone from the new GitHub repository beside the live application directory.
- Copy only ignored runtime state required by production, including `deploy/darkambient/.env`, the credential handoff file when retained, and `deploy/darkambient/data`.
- Replace `/opt/darkambient-temp-mail/app` with the verified clone using a directory swap, retaining the previous directory as a rollback copy.
- Configure the VPS checkout on `main` tracking `origin/main`.
- Rebuild and restart only the application services defined by the DarkAmbient Compose project, then verify container health and the public HTTPS health endpoint.
- Keep mail data and secrets outside Git. A code pull must not overwrite runtime state.

## Maintenance Workflow

The normal update path is:

1. Edit and test in `C:\Users\Cong-PC\Desktop\temp.darkambient.co`.
2. Commit and push to `origin/main`.
3. On the VPS, fast-forward `/opt/darkambient-temp-mail/app` to `origin/main`.
4. Rebuild and redeploy the app.
5. Require a successful container status and `/api/health` response before considering the update complete.

The deployment runbook will document this workflow and the rollback directory.

## Verification

- Add regression coverage for the DarkAmbient wordmark, metadata, SVG accessibility text, and absence of the visible `LushMail` brand in active admin/user surfaces.
- Run the complete backend test suite, Python compilation, JavaScript syntax checks, and `git diff --check`.
- Inspect the rendered desktop admin header and login/user brand surfaces without changing their established layout.
- Verify the public site serves the new logo and wordmark after deployment.
- Verify the new local checkout and VPS checkout are clean, on `main`, and tracking the new `origin/main`.
- Verify the GitHub repository is public and contains no runtime secrets or mail data.

## Rollback

- Keep the pre-conversion VPS application directory until the new checkout passes health and UI checks.
- If deployment verification fails, restore the previous directory and restart the existing Compose project with its preserved runtime state.
- DNS, mailserver data, Google Workspace MX records, and the current mail routing are outside this branding/repository change and must remain unchanged.
