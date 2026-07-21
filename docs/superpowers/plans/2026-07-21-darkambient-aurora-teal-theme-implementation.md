# DarkAmbient Aurora Teal Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thay toàn bộ hệ màu thương hiệu cam của DarkAmbient bằng Aurora Teal trên admin, user inbox và logo, rồi push `main` và deploy VPS.

**Architecture:** Giữ nguyên contract `lush-50` đến `lush-900` để không đổi cấu trúc HTML hay component. Đổi bảng màu Tailwind, màu hard-coded và SVG theo một mapping duy nhất; dùng branding test làm regression gate, sau đó kiểm tra syntax, full pytest và visual trên local trước khi merge/deploy.

**Tech Stack:** Vanilla HTML/CSS/JavaScript, Tailwind CDN config, SVG, FastAPI pytest, Git, Docker Compose/VPS helper.

## Global Constraints

- Primary `#0F766E`, hover/strong `#115E59`, surface `#F0FDFA`.
- Giữ nguyên layout, API contract, auth và toàn bộ mail behavior.
- Giữ đỏ/rose cho lỗi và destructive actions, amber cho OTP, màu Google cho translation status.
- Không thêm dependency, bundler, component hoặc animation mới.
- Production chỉ deploy từ `main`; VPS checkout canonical là `/opt/darkambient-temp-mail/app`.

---

### Task 1: Tạo regression gate cho Aurora Teal

**Files:**
- Modify: `backend/tests/test_branding.py`

**Interfaces:**
- Consumes: Các static asset ở root repo.
- Produces: Regression assertions cho palette, logo, asset cache version và việc loại bỏ brand orange.

- [ ] **Step 1: Viết test thất bại**

Thêm các hằng và assertions sau vào `backend/tests/test_branding.py`:

```python
AURORA_TEAL = {
    "50": "#f0fdfa",
    "100": "#ccfbf1",
    "200": "#99f6e4",
    "300": "#5eead4",
    "400": "#2dd4bf",
    "500": "#0f766e",
    "600": "#115e59",
    "700": "#134e4a",
    "800": "#0f3d3a",
    "900": "#082f2d",
}

OLD_BRAND_ORANGE = (
    "#fff7f5", "#fff0eb", "#ffd9cc", "#ffb8a3", "#ff8c6b",
    "#ff5528", "#e64a20", "#cc3f18", "#a33010", "#7a2008",
)


def test_active_surfaces_use_aurora_teal_theme():
    index_html = read("index.html").lower()
    user_html = read("user.html").lower()

    for shade, value in AURORA_TEAL.items():
        assert f"{shade}: '{value}'" in index_html
        assert f"{shade}: '{value}'" in user_html

    assert "style.css?v=20260721-aurora-teal" in index_html
    assert "user.css?v=20260721-aurora-teal" in user_html
    assert "logo.svg?v=20260721-aurora-teal" in index_html
    assert "logo.svg?v=20260721-aurora-teal" in user_html


def test_brand_orange_is_removed_from_active_assets():
    active_assets = "\n".join(
        read(name).lower()
        for name in ("index.html", "user.html", "style.css", "user.css", "app.js", "user.js", "logo.svg")
    )
    for old_value in OLD_BRAND_ORANGE:
        assert old_value not in active_assets
```

Cập nhật `test_logo_is_accessible_darkambient_monogram` để assert:

```python
assert "DA monogram" in logo
assert "teal" in logo
assert '#0f766e' in logo.lower()
assert '#ff5528' not in logo.lower()
```

- [ ] **Step 2: Chạy test để xác nhận RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_branding.py -q
```

Expected: FAIL tại palette/cache/logo assertions vì source vẫn dùng màu cam.

- [ ] **Step 3: Commit test RED cùng implementation ở Task 2**

Không commit test đỏ riêng lên shared branch; giữ thay đổi trong worktree và chuyển sang Task 2.

---

### Task 2: Áp dụng Aurora Teal lên active UI assets

**Files:**
- Modify: `index.html`
- Modify: `user.html`
- Modify: `style.css`
- Modify: `user.css`
- Modify: `app.js`
- Modify: `user.js`
- Modify: `logo.svg`

**Interfaces:**
- Consumes: Contract class `lush-*` và selectors hiện hữu.
- Produces: Cùng component/layout với palette Aurora Teal và cache version mới.

- [ ] **Step 1: Đổi bảng màu Tailwind và cache version**

Trong cả `index.html` và `user.html`, thay object `lush` bằng:

```javascript
lush: {
  50: '#f0fdfa',
  100: '#ccfbf1',
  200: '#99f6e4',
  300: '#5eead4',
  400: '#2dd4bf',
  500: '#0f766e',
  600: '#115e59',
  700: '#134e4a',
  800: '#0f3d3a',
  900: '#082f2d',
}
```

Đổi mọi query `logo.svg?v=20260721-darkambient-brand` thành `logo.svg?v=20260721-aurora-teal`, `style.css?...` thành `style.css?v=20260721-aurora-teal`, và `user.css?...` thành `user.css?v=20260721-aurora-teal`.

- [ ] **Step 2: Đổi màu brand hard-coded**

Áp dụng mapping sau cho active UI assets, không đổi semantic OTP `#fff7ed`/`#c2410c`, rose/red hay Google colors:

```text
#fff7f5 -> #f0fdfa
#fff0eb -> #ccfbf1
#ffd9cc -> #99f6e4
#ffb8a3 -> #5eead4
#ff8c6b -> #2dd4bf
#ff5528 -> #0f766e
#e64a20 -> #115e59
#cc3f18 -> #134e4a
#a33010 -> #0f3d3a
#7a2008 -> #082f2d
#fffaf8 -> #f8fffd
#fff7f3 -> #f0fdfa
#fff7f2 -> #ecfdf9
#fffbf8 -> #f8fffd
#fffdfa -> #fbfffe
#fffdfb -> #fbfffe
#ff9f85 -> #5eead4
#ff7b57 -> #14b8a6
#ff784f -> #14b8a6
#ff6b43 -> #0d9488
rgba(255, 85, 40, A) -> rgba(15, 118, 110, A)
```

Trong avatar palettes, đổi brand orange `#f97316` thành `#0d9488` và `#fffaf4` thành `#f0fdfa`; giữ các palette avatar xanh/pink khác để danh sách mail vẫn phân biệt được người gửi.

- [ ] **Step 3: Đổi logo SVG**

Giữ nguyên paths và accessibility title. Đổi mô tả thành `Stylized DA monogram in teal` và fill thành `#0f766e`.

- [ ] **Step 4: Chạy test để xác nhận GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests/test_branding.py -q
node --check .\app.js
node --check .\user.js
```

Expected: branding tests PASS, hai syntax checks exit code 0.

- [ ] **Step 5: Commit theme implementation**

```powershell
git add -- backend/tests/test_branding.py index.html user.html style.css user.css app.js user.js logo.svg
git commit -m "feat: apply Aurora Teal theme"
```

---

### Task 3: Cập nhật canonical docs và xác minh toàn bộ app

**Files:**
- Modify: `docs/UI_SYSTEM.md`
- Modify: `docs/CHANGELOG.md`

**Interfaces:**
- Consumes: Theme đã pass regression test.
- Produces: Canonical UI documentation và release record khớp source.

- [ ] **Step 1: Cập nhật UI system**

Đổi mô tả orange thành Aurora Teal và ghi rõ:

```markdown
- Primary actions use Aurora Teal `#0f766e`; hover uses `#115e59`; subtle brand surfaces use `#f0fdfa`.
- Semantic rose/red, amber OTP, Google translation colors, and the marine user hero remain independent of the brand palette.
```

- [ ] **Step 2: Append changelog**

Thêm một entry ngày `2026-07-21` mô tả admin/user/logo đã chuyển sang Aurora Teal, không đổi mail behavior.

- [ ] **Step 3: Chạy full verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Get-ChildItem .\backend\app\*.py | ForEach-Object { .\.venv\Scripts\python.exe -m py_compile $_.FullName }
node --check .\app.js
node --check .\user.js
git diff --check HEAD~1
```

Expected: pytest 0 failures, syntax checks exit code 0, `git diff --check` không có output.

- [ ] **Step 4: Visual QA local**

Chạy app local tại `127.0.0.1:8010`, kiểm tra admin và user inbox ở desktop/mobile. Xác nhận logo, wordmark, primary button, active row, focus state và reader surfaces dùng teal; semantic OTP/error vẫn đúng vai trò; không có regression layout.

- [ ] **Step 5: Commit docs**

```powershell
git add -- docs/UI_SYSTEM.md docs/CHANGELOG.md
git commit -m "docs: record Aurora Teal UI system"
```

---

### Task 4: Merge, publish và deploy VPS

**Files:**
- No source files; Git/GitHub/VPS operations only.

**Interfaces:**
- Consumes: Nhánh `codex/aurora-teal` đã verify.
- Produces: `origin/main` và VPS checkout chạy cùng commit.

- [ ] **Step 1: Merge fast-forward vào main**

```powershell
git switch main
git merge --ff-only codex/aurora-teal
```

- [ ] **Step 2: Push main**

```powershell
git push origin main
```

Expected: `origin/main` trỏ tới commit theme/docs mới.

- [ ] **Step 3: Deploy bằng VPS checkout hiện hữu**

SSH vào VPS, chạy:

```bash
lushtempmail update
lushtempmail status
```

Nếu helper không có trong non-interactive PATH, chạy `/usr/local/bin/lushtempmail update` và `/usr/local/bin/lushtempmail status`.

- [ ] **Step 4: Production verification**

Xác nhận `https://temp.darkambient.co/` trả HTTP 200, asset version Aurora Teal xuất hiện trong HTML, logo/CSS mới tải thành công, và admin/user login + inbox vẫn hoạt động.

- [ ] **Step 5: Báo cáo release**

Ghi lại branch, commit cuối, test count, URL production và trạng thái VPS. Không tuyên bố hoàn tất nếu bất kỳ verification nào chưa có output thành công mới.
