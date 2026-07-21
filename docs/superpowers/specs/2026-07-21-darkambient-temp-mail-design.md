# Darkambient Temp Mail Design

## Mục tiêu

Triển khai một hệ thống temp mail độc lập trên VPS `89.117.21.223` với:

- giao diện quản lý tại `https://temp.darkambient.co`;
- địa chỉ nhận mail dạng `anything@temp.darkambient.co`;
- đầy đủ chức năng nhận, gửi, reply và forward;
- giữ nguyên Google Workspace và toàn bộ MX hiện tại của `darkambient.co`.

## Phạm vi

Hệ thống mới chỉ quản lý namespace `temp.darkambient.co`. Không thay đổi MX, mailbox hoặc luồng gửi/nhận của địa chỉ `@darkambient.co`.

Ứng dụng sử dụng mã nguồn `Lush-Temp-Mail` hiện tại. Mail runtime mới dùng Docker Mailserver; Nginx hiện có trên VPS tiếp tục sở hữu cổng `80/443` và reverse proxy giao diện web.

## Kiến trúc

### Thành phần

1. **Nginx host**
   - Phục vụ `temp.darkambient.co` qua HTTPS.
   - Reverse proxy tới ứng dụng trên loopback hoặc Docker network, không công khai cổng ứng dụng.

2. **Lush-Temp-Mail app**
   - FastAPI + SQLite + static HTML/CSS/JS.
   - Đọc mailbox trung tâm qua IMAP.
   - Tự phát hiện alias gốc từ `X-Original-To`, `Delivered-To` hoặc các recipient header được parser hỗ trợ.
   - Gửi, reply và forward qua SMTP có xác thực.

3. **Docker Mailserver**
   - Postfix nhận SMTP cho `temp.darkambient.co`.
   - Dovecot cung cấp mailbox trung tâm `contact@temp.darkambient.co` cho app qua network nội bộ.
   - Catch-all chuyển mọi địa chỉ `@temp.darkambient.co` vào mailbox trung tâm, đồng thời giữ recipient gốc trong header.
   - SMTP outbound ký DKIM; relay chỉ cho phép client nội bộ đã xác thực.
   - Bật cơ chế chống brute force và lọc spam phù hợp với tài nguyên VPS.

4. **Persistent data**
   - SQLite của app, mail data, mail state, cấu hình generated và secrets nằm trong các volume/thư mục riêng dưới `/opt/darkambient-temp-mail`.
   - Secrets chỉ tồn tại trên VPS, không commit vào Git.

### Network và cổng

- Công khai: `22/tcp`, `25/tcp`, `80/tcp`, `443/tcp`.
- Không công khai cho Internet: app port `8010`, IMAP `993`, SMTP submission `587`.
- App truy cập IMAP/SMTP qua Docker network nội bộ.
- Firewall cho phép SSH trước khi bật policy chặn inbound mặc định.

## Domain và DNS

Các record mới:

- `A temp.darkambient.co -> 89.117.21.223` cho web app.
- `A mx.temp.darkambient.co -> 89.117.21.223`, bắt buộc DNS-only.
- `MX temp.darkambient.co 10 mx.temp.darkambient.co`.
- `TXT temp.darkambient.co` chứa SPF chỉ cho phép mail server mới gửi.
- `TXT mail._domainkey.temp.darkambient.co` chứa DKIM public key do mail stack tạo.
- `TXT _dmarc.temp.darkambient.co` chứa DMARC policy khởi đầu ở chế độ theo dõi, sau đó có thể siết chặt khi delivery ổn định.

Record MX của apex `darkambient.co` tiếp tục trỏ Google Workspace và không bị chỉnh sửa.

PTR/rDNS của `89.117.21.223` cần đổi từ hostname mặc định của nhà cung cấp sang `mx.temp.darkambient.co`. Forward DNS của hostname này phải trỏ ngược về cùng IP.

## Luồng dữ liệu

### Nhận mail

1. Sender tra MX của `temp.darkambient.co` và gửi tới `mx.temp.darkambient.co:25`.
2. Postfix kiểm tra recipient thuộc domain được quản lý và chuyển catch-all vào `contact@temp.darkambient.co`.
3. Dovecot lưu message, giữ header thể hiện recipient gốc.
4. App nhận thông báo IMAP IDLE hoặc polling fallback, parse alias gốc và lưu nội dung/OTP/link/attachment vào SQLite.
5. Admin hoặc user đã đăng nhập xem message tại `temp.darkambient.co`.

### Gửi, reply và forward

1. Admin thao tác trong web app.
2. App xác thực input và dựng message; reply giữ `In-Reply-To`/`References`, forward đính kèm attachment khi có.
3. App đăng nhập SMTP nội bộ bằng mailbox trung tâm.
4. Postfix ký DKIM, áp dụng rate limit và gửi trực tiếp tới MX đích.
5. App lưu sent-message metadata và attachment cần thiết trong SQLite.

## Authentication và chống lạm dụng

- Giữ mô hình hai role hiện tại: `admin` và `user`.
- Tạo mật khẩu ngẫu nhiên mạnh, khác nhau cho admin, user, IMAP và SMTP.
- Cookie chỉ gửi qua HTTPS; session có thời hạn hữu hạn.
- Không public registration và không anonymous SMTP submission.
- Chỉ admin được dùng send/reply/forward theo contract hiện tại.
- Postfix không được cấu hình open relay.
- Giới hạn tốc độ outbound để giảm rủi ro tài khoản hoặc giao diện bị lạm dụng.
- SSH tiếp tục dùng tài khoản hiện có trong giai đoạn triển khai; sau khi xác minh có thể chuyển sang key-only ở một task bảo mật riêng.

## TLS

- Nginx dùng Let's Encrypt certificate cho `temp.darkambient.co`.
- Mail hostname dùng certificate hợp lệ cho `mx.temp.darkambient.co` khi cần TLS ở mail transport.
- Việc cấp certificate chỉ thực hiện sau khi A record đã resolve đúng về VPS.
- Certificate được tự động renew; deploy verification kiểm tra cả expiry và hostname match.

## Xử lý lỗi

- Nếu IMAP mất kết nối, app ghi log và fallback về polling thay vì làm API crash.
- Nếu SMTP outbound lỗi, API trả lỗi rõ ràng và không ghi nhận message là đã gửi thành công.
- Container dùng restart policy và health check.
- Nginx chỉ được reload sau khi `nginx -t` thành công.
- Firewall chỉ được bật sau khi rule SSH đã tồn tại và một phiên SSH dự phòng vẫn đang hoạt động.
- Nếu DNS chưa cập nhật, mail stack và app vẫn được kiểm tra nội bộ; public TLS và inbound end-to-end được đánh dấu chờ DNS thay vì giả định đã hoạt động.

## Triển khai và rollback

1. Chụp trạng thái Nginx, port, package và tạo backup cấu hình liên quan.
2. Cài Docker Engine/Compose từ nguồn package phù hợp với Ubuntu 24.04.
3. Tạo mail stack, mailbox trung tâm, catch-all, DKIM và secrets.
4. Deploy app với env cho `temp.darkambient.co` làm cả web domain và mail-address domain.
5. Thêm Nginx virtual host, kiểm tra cấu hình rồi reload.
6. Áp dụng DNS và PTR/rDNS.
7. Cấp TLS, bật firewall và chạy verification end-to-end.

Rollback giữ nguyên Google Workspace. Có thể dừng các container mới, khôi phục Nginx backup và xóa các DNS record dưới `temp.darkambient.co` mà không ảnh hưởng apex MX.

## Verification và tiêu chí hoàn thành

- `darkambient.co` vẫn trả về bộ MX Google Workspace ban đầu.
- `temp.darkambient.co` trả HTTPS hợp lệ và chỉ hiển thị app sau đăng nhập.
- Login admin và user hoạt động; role routing đúng.
- Gửi thử từ một hệ thống ngoài tới alias chưa pre-create tại `@temp.darkambient.co` xuất hiện đúng alias trong app.
- OTP/link parsing và attachment download hoạt động trên mail nhận thử.
- Send mới, reply và forward tới mailbox ngoài đều thành công; header DKIM pass.
- SPF, DKIM và DMARC có thể được truy vấn công khai.
- SMTP relay test từ nguồn không xác thực bị từ chối.
- App port, IMAP và SMTP submission không truy cập được từ Internet.
- Container health, log, restart policy, certificate renewal và backup path đều được kiểm tra.

## Phần việc cần chủ domain thực hiện

- Cho phép thêm các DNS record đã liệt kê trong Cloudflare hoặc tự thêm theo giá trị triển khai cung cấp.
- Đổi PTR/rDNS tại control panel của nhà cung cấp VPS sang `mx.temp.darkambient.co` nếu VPS không cung cấp API/CLI có sẵn trên máy.
