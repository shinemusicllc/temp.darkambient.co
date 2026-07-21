# DarkAmbient Aurora Teal Theme Design

## Mục tiêu

Thay hệ màu thương hiệu cam hiện tại của DarkAmbient bằng phương án C — Aurora Teal, đồng bộ trên admin shell, user inbox và logo, đồng thời giữ nguyên layout, mật độ thông tin và toàn bộ hành vi gửi/nhận/reply/forward hiện có.

## Phạm vi

- Đổi bảng màu `lush` trong `index.html` và `user.html` sang Aurora Teal để các utility class hiện hữu tự nhận theme mới.
- Đổi các giá trị cam hard-coded trong `style.css`, `user.css`, `app.js`, `user.js` sang token Aurora Teal tương ứng.
- Đổi màu monogram trong `logo.svg` và cập nhật mô tả accessibility từ orange sang teal.
- Cập nhật cache-busting query của CSS và logo để trình duyệt/VPS lấy asset mới sau deploy.
- Cập nhật `docs/UI_SYSTEM.md`, branding test và changelog để theme mới có canonical documentation.

Không thay đổi cấu trúc HTML, API contract, backend mail runtime, DNS, nội dung email, auth hay luồng điều hướng.

## Bảng màu chuẩn

| Token | Giá trị | Vai trò |
| --- | --- | --- |
| `lush-50` | `#F0FDFA` | Brand surface, active row nhẹ |
| `lush-100` | `#CCFBF1` | Selected/unread surface |
| `lush-200` | `#99F6E4` | Border nhấn nhẹ |
| `lush-300` | `#5EEAD4` | Focus border |
| `lush-400` | `#2DD4BF` | Accent phụ |
| `lush-500` | `#0F766E` | Primary action và logo |
| `lush-600` | `#115E59` | Hover/strong action |
| `lush-700` | `#134E4A` | Text accent đậm |
| `lush-800` | `#0F3D3A` | Dark accent |
| `lush-900` | `#082F2D` | Deepest accent |

Ba giá trị được người dùng duyệt trực tiếp là `#F0FDFA`, `#0F766E` và `#115E59`; các shade còn lại mở rộng theo cùng hue để giữ contract `lush-50` đến `lush-900` hiện hữu.

## Quy tắc ánh xạ visual

- Logo `DA`, wordmark accent, primary button, active navigation, focus ring, link thương hiệu và selected state dùng Aurora Teal.
- Các surface ấm như `#fff7f5`, `#fff0eb`, `#fffdfa` và `#fffaf8` chuyển sang các surface teal/trắng trung tính gần nhất.
- Gradient thương hiệu cam chuyển thành gradient teal, với đầu sáng dùng `#14B8A6` hoặc `#2DD4BF` và đầu đậm dùng `#0F766E`.
- Nền marine đậm của hero user inbox được giữ nguyên để bảo toàn cấu trúc visual; nút tìm kiếm và các điểm nhấn bên trong chuyển sang teal.
- Màu semantic không thuộc thương hiệu được giữ nguyên: đỏ/rose cho lỗi và hành động nguy hiểm, amber cho OTP, xanh Google cho translation status.
- Không thêm card, badge trang trí, shadow mới, animation mới hoặc thay đổi border radius.

## Thành phần và file chịu tác động

- `index.html`: bảng màu Tailwind, asset version, admin primary/focus utilities.
- `user.html`: bảng màu Tailwind, asset version, user lookup primary/focus utilities.
- `style.css`: active folder, unread/recent row, compose controls, chips, pagination, translation controls và brand gradients.
- `user.css`: selected message, reader surface, accent text và interactive states.
- `app.js`, `user.js`: avatar palette brand và link accent dựng động.
- `logo.svg`: fill và mô tả màu.
- `backend/tests/test_branding.py`: regression test cho palette, logo và cache version.
- `docs/UI_SYSTEM.md`: canonical visual language sau thay đổi.

## Trạng thái tương tác

- Primary default: `#0F766E` với chữ trắng.
- Primary hover: `#115E59` với chữ trắng.
- Focus border/ring: `#5EEAD4` hoặc alpha của `#0F766E` theo pattern đang có.
- Active/selected surface: `#F0FDFA` hoặc `#CCFBF1`, kèm border/text `#0F766E` hoặc `#134E4A`.
- Disabled state tiếp tục dùng slate/opacity hiện hữu, không tô teal mạnh.

## Kiểm thử và tiêu chí chấp nhận

1. Branding test phải thất bại trước khi implementation vì vẫn tìm palette cam, sau đó pass khi toàn bộ token và logo chuyển sang Aurora Teal.
2. Không còn giá trị brand orange cũ trong `index.html`, `user.html`, `style.css`, `user.css`, `app.js`, `user.js` và `logo.svg`; ngoại lệ duy nhất là các màu semantic amber/rose không đại diện thương hiệu.
3. `node --check app.js` và `node --check user.js` pass.
4. Toàn bộ pytest pass, không thay đổi API/mail behavior.
5. Kiểm tra trực quan desktop và mobile xác nhận logo, wordmark, primary button, active row, focus state và detail surfaces đồng bộ teal; text vẫn có contrast rõ trên nền trắng/marine.
6. Production chỉ được deploy sau khi local verification hoàn tất; deploy dùng checkout `main` hiện có trên VPS và helper `lushtempmail update`.

## Rollback

Rollback bằng commit revert của thay đổi theme rồi chạy lại `lushtempmail update`. Không cần rollback database, mail runtime hoặc DNS vì thiết kế không đụng các lớp đó.
