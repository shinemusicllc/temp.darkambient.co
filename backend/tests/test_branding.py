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
    assert 'Dark<span class="text-lush-500">Ambient</span>' in index_html
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


def test_runtime_defaults_use_darkambient_identity():
    config = read("backend/app/config.py")
    main = read("backend/app/main.py")
    translator = read("backend/app/translator.py")
    env_example = read("deploy/darkambient/app.env.example")

    assert 'os.getenv("TEMPMAIL_PUBLIC_DOMAIN", "temp.darkambient.co")' in config
    assert 'os.getenv("TEMPMAIL_MAIL_DOMAIN", "temp.darkambient.co")' in config
    assert 'os.getenv("IMAP_HOST", "mx.temp.darkambient.co")' in config
    assert 'os.getenv("SMTP_FROM_NAME", "DarkAmbient")' in config
    assert 'FastAPI(title="DarkAmbient Temp Mail"' in main
    assert '"User-Agent": "DarkAmbient/1.0"' in translator
    assert "SMTP_FROM_NAME=DarkAmbient" in env_example
