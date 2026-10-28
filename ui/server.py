"""Loopback-only demo UI. Azure authentication and conversation state stay server-side."""

import argparse
import json
import logging
import os
import secrets
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

ROOT = Path(__file__).parent
logger = logging.getLogger(__name__)
credential = DefaultAzureCredential()
sessions: dict[str, dict] = {}
sessions_lock = threading.Lock()


class RequestBlockedError(ValueError):
    """The upstream safety filter rejected the request, not an infrastructure failure."""


def response_text(payload: dict) -> str:
    if (
        payload.get("status") == "incomplete"
        and (payload.get("incomplete_details") or {}).get("reason") == "content_filter"
    ):
        raise RequestBlockedError("The hosted service blocked this request.")
    if payload.get("status") != "completed":
        raise ValueError("The hosted agent did not complete the response.")
    parts = [
        content["text"]
        for item in payload.get("output", [])
        if item.get("type") == "message" and item.get("role") == "assistant"
        for content in item.get("content", [])
        if content.get("type") == "output_text" and isinstance(content.get("text"), str)
    ]
    text = "\n".join(parts).strip()
    if not text:
        raise ValueError("The hosted agent returned no assistant text.")
    return text


def invoke(messages: list[dict]) -> str:
    token = credential.get_token("https://ai.azure.com/.default").token
    request = Request(
        os.environ["NORTHSTAR_AGENT_RESPONSES_ENDPOINT"],
        data=json.dumps({"input": messages, "stream": False, "store": False}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=180) as response:
        return response_text(json.load(response))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s %s", self.command, self.path)

    def send_body(
        self, code: int, body: bytes, content_type: str, cookie: str | None = None
    ):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; connect-src 'self'; "
            "object-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def json_response(self, code: int, payload: dict, cookie: str | None = None):
        self.send_body(code, json.dumps(payload).encode(), "application/json", cookie)

    def allowed_host(self) -> bool:
        return self.headers.get("Host") in {
            f"127.0.0.1:{self.server.server_port}",
            f"localhost:{self.server.server_port}",
        }

    def do_GET(self):
        if not self.allowed_host():
            return self.json_response(403, {"error": "Loopback access only."})
        if self.path.split("?")[0] == "/":
            return self.send_body(
                200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8"
            )
        if self.path == "/health":
            return self.json_response(
                200, {"status": "ready", "mode": "remote-hosted-agent"}
            )
        self.json_response(404, {"error": "Not found."})

    def do_POST(self):
        origin = self.headers.get("Origin")
        allowed_origins = {
            f"http://127.0.0.1:{self.server.server_port}",
            f"http://localhost:{self.server.server_port}",
        }
        if not self.allowed_host() or origin not in allowed_origins:
            return self.json_response(
                403, {"error": "Same-origin loopback requests only."}
            )
        if self.path == "/api/chat/reset":
            cookie = SimpleCookie()
            cookie.load(self.headers.get("Cookie", ""))
            session_id = cookie["northstar"].value if "northstar" in cookie else ""
            with sessions_lock:
                session = sessions.get(session_id)
                if session:
                    if session["busy"]:
                        return self.json_response(
                            409, {"error": "Please wait for the current reply."}
                        )
                    session["messages"] = []
                    session["updated"] = time.monotonic()
            return self.json_response(200, {"status": "reset"})
        if self.path != "/api/chat":
            return self.json_response(404, {"error": "Not found."})
        if self.headers.get_content_type() != "application/json":
            return self.json_response(415, {"error": "Send application/json."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 8192:
                return self.json_response(
                    413, {"error": "Request is too large or empty."}
                )
            payload = json.loads(self.rfile.read(length))
            message = payload.get("message") if isinstance(payload, dict) else None
            if not isinstance(message, str) or not 1 <= len(message.strip()) <= 2000:
                return self.json_response(
                    400, {"error": "Enter a message of 1-2000 characters."}
                )
        except (ValueError, UnicodeDecodeError):
            return self.json_response(400, {"error": "Invalid JSON request."})
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))
        session_id = cookie["northstar"].value if "northstar" in cookie else ""
        now = time.monotonic()
        with sessions_lock:
            expired = [
                key for key, value in sessions.items() if now - value["updated"] > 1800
            ]
            for key in expired:
                del sessions[key]
            if session_id not in sessions:
                if len(sessions) >= 64:
                    return self.json_response(
                        429, {"error": "Demo session limit reached. Try later."}
                    )
                session_id = secrets.token_urlsafe(32)
                sessions[session_id] = {
                    "messages": [],
                    "updated": now,
                    "busy": False,
                    "calls": [],
                }
            session = sessions[session_id]
            session["calls"] = [t for t in session["calls"] if now - t < 60]
            if session["busy"] or len(session["calls"]) >= 10:
                return self.json_response(
                    429, {"error": "Please wait before sending another message."}
                )
            if len(session["messages"]) >= 40:
                return self.json_response(
                    429,
                    {"error": "Conversation limit reached. Select New chat to start again."},
                )
            session["busy"] = True
            session["updated"] = now
            session["calls"].append(now)
            messages = [
                *session["messages"],
                {"role": "user", "content": message.strip()},
            ]
        try:
            answer = invoke(messages)
            with sessions_lock:
                session["messages"] = [
                    *messages,
                    {"role": "assistant", "content": answer},
                ]
                session["updated"] = time.monotonic()
            code, payload = 200, {"reply": answer}
        except RequestBlockedError:
            logger.info("Hosted-agent request rejected by content filter")
            code, payload = 422, {
                "error": "I can't help with that request. Please ask about an order or our return policy."
            }
        except (HTTPError, URLError, TimeoutError, ValueError):
            logger.exception("Hosted-agent request failed")
            code, payload = 502, {
                "error": "The hosted agent could not complete this request. Check the server logs and retry."
            }
        except Exception:
            logger.exception("Unexpected authentication or hosted-agent failure")
            code, payload = 502, {
                "error": "The hosted agent is unavailable. Check Azure authentication and server logs."
            }
        finally:
            with sessions_lock:
                session["busy"] = False
        return self.json_response(
            code,
            payload,
            f"northstar={session_id}; HttpOnly; SameSite=Strict; Path=/; Max-Age=1800",
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7071)
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    endpoint = os.environ.get("NORTHSTAR_AGENT_RESPONSES_ENDPOINT", "")
    parsed = urlparse(endpoint)
    if (
        parsed.scheme != "https"
        or not (parsed.hostname or "").endswith(".services.ai.azure.com")
        or not parsed.path.endswith("/protocols/openai/responses")
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise RuntimeError(
            "Set NORTHSTAR_AGENT_RESPONSES_ENDPOINT to the exact deployed HTTPS Responses endpoint."
        )
    logging.basicConfig(level=logging.INFO)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    logger.info(
        "Northstar demo UI: http://127.0.0.1:%s (real hosted agent; synthetic orders)",
        args.port,
    )
    try:
        server.serve_forever()
    finally:
        server.server_close()
        credential.close()


if __name__ == "__main__":
    main()
