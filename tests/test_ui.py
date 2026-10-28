import importlib.util
import json
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

spec = importlib.util.spec_from_file_location(
    "northstar_ui", Path(__file__).parents[1] / "ui/server.py"
)
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)


@pytest.fixture
def proxy(monkeypatch):
    ui.sessions.clear()
    calls = []

    def fake_invoke(messages):
        calls.append(messages)
        return "Test response, not a real agent invocation."

    monkeypatch.setattr(ui, "invoke", fake_invoke)
    server = ui.ThreadingHTTPServer(("127.0.0.1", 0), ui.Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    yield base, calls
    server.shutdown()
    server.server_close()
    thread.join()


def post(base, body, *, origin=None, cookie=None):
    headers = {"Content-Type": "application/json", "Origin": origin or base}
    if cookie:
        headers["Cookie"] = cookie
    request = Request(
        base + "/api/chat", data=json.dumps(body).encode(), headers=headers
    )
    return urlopen(request, timeout=5)


def test_page_contains_no_remote_configuration(proxy):
    base, _ = proxy
    with urlopen(base) as result:
        html = result.read().decode()
    assert "Northstar Support" in html
    assert "services.ai.azure.com" not in html


def test_customer_copy_uses_one_workshop_disclosure(proxy):
    base, _ = proxy
    with urlopen(base) as result:
        html = result.read().decode()
    assert "Need a hand with an order or a return?" in html
    assert html.count("Workshop demonstration.") == 1
    assert "demo order" not in html
    assert "Built for the workshop" not in html
    assert "hosted agent" not in html
    assert "cold start" not in html


def test_chat_preserves_history_server_side(proxy):
    base, calls = proxy
    with post(base, {"message": "Can I return something?"}) as response:
        cookie = response.headers["Set-Cookie"].split(";")[0]
        assert "HttpOnly" in response.headers["Set-Cookie"]
        assert json.load(response)["reply"].startswith("Test response")
    with post(base, {"message": "CHI1001, unopened"}, cookie=cookie):
        pass
    assert [message["role"] for message in calls[1]] == ["user", "assistant", "user"]
    assert calls[1][-1]["content"] == "CHI1001, unopened"


def test_cross_origin_is_blocked(proxy):
    base, calls = proxy
    with pytest.raises(HTTPError) as error:
        post(base, {"message": "hello"}, origin="https://untrusted.example")
    assert error.value.code == 403
    assert not calls


@pytest.mark.parametrize(
    "body", [{}, {"message": []}, {"message": " "}, {"message": "x" * 2001}]
)
def test_invalid_input_is_explicit(proxy, body):
    base, calls = proxy
    with pytest.raises(HTTPError) as error:
        post(base, body)
    assert error.value.code == 400
    assert not calls


def test_private_files_are_not_served(proxy):
    base, _ = proxy
    with pytest.raises(HTTPError) as error:
        urlopen(base + "/.env")
    assert error.value.code == 404


def test_upstream_error_is_not_a_fake_answer(proxy, monkeypatch):
    base, _ = proxy

    def fail(_):
        raise ValueError("Missing completion")

    monkeypatch.setattr(ui, "invoke", fail)
    with pytest.raises(HTTPError) as error:
        post(base, {"message": "hello"})
    assert error.value.code == 502
    assert "error" in json.load(error.value)


def test_response_shape_requires_completion():
    with pytest.raises(ValueError, match="complete"):
        ui.response_text({"status": "failed", "output": []})
    with pytest.raises(ValueError, match="no assistant text"):
        ui.response_text({"status": "completed", "output": []})
    assert (
        ui.response_text(
            {
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "Hi"}],
                    }
                ],
            }
        )
        == "Hi"
    )
