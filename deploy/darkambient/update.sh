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
curl --fail --silent --show-error --retry 12 --retry-delay 2 --retry-all-errors \
  https://temp.darkambient.co/api/health
docker compose -f compose.yaml ps
