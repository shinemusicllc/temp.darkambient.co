## Backend Rules

- Backend dùng Python + FastAPI, tránh thêm ORM nặng nếu SQLite stdlib đã đủ.
- Mọi logic sync mail, session admin, OTP/link extraction phải ở `backend/app/`, không để trong `app.js`.
- Nếu thay đổi env contract hoặc schema SQLite, cập nhật `deploy/darkambient/app.env.example` và `deploy/darkambient/README.md` cùng lúc.

## Backend Commands

- Dev server: chạy từ root repo với `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8010 --reload`.
- Tests: chạy từ root repo với `python -m pytest backend/tests -q`.

## Safety

- Không commit password IMAP/SMTP thật vào repo.
- Không để sync loop crash toàn app khi IMAP lỗi; log và retry.
- Luôn giữ khả năng auto-discover alias từ inbound mail, kể cả khi alias chưa từng được tạo thủ công.
