## Deploy Rules

- Deploy stack chỉ phụ trách `temp.darkambient.co`; không thay đổi MX Google Workspace của apex `darkambient.co`.
- Nginx host sở hữu `80/443`; app chỉ bind `127.0.0.1:8012 -> container 8010` và SMTP server public duy nhất cổng `25`.
- Password, database, mailbox data, DKIM/TLS private key chỉ tồn tại trong runtime path đã ignore trên VPS, không commit.
- VPS checkout `/opt/darkambient-temp-mail/app` phải tracking `origin/main` của repo độc lập `temp.darkambient.co`.

## Commands

- Compose: `cd /opt/darkambient-temp-mail/app/deploy/darkambient && docker compose -f compose.yaml up -d --build`.
- Update: `cd /opt/darkambient-temp-mail/app && sudo bash deploy/darkambient/update.sh`.
