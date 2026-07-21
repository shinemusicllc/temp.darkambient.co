from pathlib import Path

from backend.app import main


ROOT = Path(__file__).resolve().parents[2]


def test_standalone_send_endpoint_sends_and_stores_message(monkeypatch):
    assert hasattr(main, "send_new_message"), "Standalone send endpoint is missing"

    captured = {}

    def fake_send_composed_message(**kwargs):
        captured.update(kwargs)
        return {
            "mode": kwargs["mode"],
            "to": ["receiver@example.com"],
            "cc": [],
            "subject": kwargs["subject"],
            "from": "contact@temp.darkambient.co",
            "message_id": "<new-message@temp.darkambient.co>",
            "attachment_count": 0,
        }

    def fake_store_sent_message(payload):
        captured["stored"] = payload
        return {"id": 1, **payload}

    monkeypatch.setattr(main, "send_composed_message", fake_send_composed_message)
    monkeypatch.setattr(main.db, "store_sent_message", fake_store_sent_message)

    result = main.send_new_message(
        {
            "to": "receiver@example.com",
            "cc": "",
            "subject": "Fresh message",
            "body": "Hello from DarkAmbient.",
        },
        _session={"username": "admin", "role": "admin"},
    )

    assert result["ok"] is True
    assert captured["source_message"] == {}
    assert captured["mode"] == "send"
    assert captured["stored"]["source_message_id"] is None
    assert captured["stored"]["mode"] == "send"


def test_admin_ui_exposes_new_message_composer():
    index_html = (ROOT / "index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "app.js").read_text(encoding="utf-8")

    assert 'id="newMessageBtn"' in index_html
    assert 'app.js?v=20260721-darkambient-compose' in index_html
    assert "function openNewMessageComposer()" in app_js
    assert "'/api/messages/send'" in app_js
