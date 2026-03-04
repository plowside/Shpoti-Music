import asyncio
import json
import logging
import secrets
import threading
import urllib.parse
import webbrowser
from typing import Any, Dict, Optional

import aiohttp
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse


CLIENT_ID = "cIYxtC61UuswkJN1H7looUKPUL3beAqj"
CLIENT_SECRET = "nyHItX1eTNfC8TpjhhVFstmo0ia4dwpU"

LOCAL_CALLBACK_HOST = "127.0.0.1"
LOCAL_CALLBACK_PORT = 9067
LOCAL_CALLBACK_PATH = "/callback"
OAUTH_WAIT_TIMEOUT_SECONDS = 180
OPEN_AUTH_URL_IN_BROWSER = True


logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


class SoundCloudApiError(RuntimeError):
    pass


class SoundCloudOAuth:
    AUTH_URL = "https://secure.soundcloud.com/authorize"
    TOKEN_URLS = (
        "https://secure.soundcloud.com/oauth/token",
        "https://api.soundcloud.com/oauth2/token",
    )

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def build_authorize_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "non-expiring",
            "state": state,
        }
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        }

        last_error: Optional[Exception] = None
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            for token_url in self.TOKEN_URLS:
                try:
                    async with session.post(token_url, data=payload, headers=headers) as resp:
                        body = await resp.text()
                        if resp.status >= 400:
                            raise SoundCloudApiError(
                                f"Token endpoint {token_url} -> HTTP {resp.status}: {body}"
                            )
                        return json.loads(body) if body else {}
                except Exception as exc:
                    last_error = exc

        raise SoundCloudApiError(f"OAuth token request failed: {last_error}")


class OAuthCallbackServer:
    def __init__(self, host: str, port: int, callback_path: str) -> None:
        self.host = host
        self.port = port
        self.callback_path = callback_path

        self._event = threading.Event()
        self._result: Dict[str, Optional[str]] = {"code": None, "state": None, "error": None}

        self.app = FastAPI()
        self.config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="warning",
            access_log=False,
            reload=False,
        )
        self.server = uvicorn.Server(self.config)
        self.thread: Optional[threading.Thread] = None

        self._bind_routes()

    def _bind_routes(self) -> None:
        @self.app.get(self.callback_path)
        async def callback(request: Request) -> HTMLResponse:
            query = request.query_params
            self._result = {
                "code": query.get("code"),
                "state": query.get("state"),
                "error": query.get("error"),
            }
            self._event.set()

            html = (
                "<html><body><h3>SoundCloud authorization complete.</h3>"
                "<p>You can close this tab and return to terminal.</p></body></html>"
            )
            return HTMLResponse(content=html, status_code=200)

        @self.app.get("/health")
        async def health() -> JSONResponse:
            return JSONResponse({"ok": True})

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self._event.clear()
        self._result = {"code": None, "state": None, "error": None}
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.server.should_exit = True
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)

    def wait_for_callback(self, timeout_seconds: int) -> Optional[Dict[str, Optional[str]]]:
        ok = self._event.wait(timeout_seconds)
        if not ok:
            return None
        return dict(self._result)


def build_local_redirect_uri() -> str:
    return f"http://localhost:{LOCAL_CALLBACK_PORT}{LOCAL_CALLBACK_PATH}"


async def authorize_and_get_token() -> str:
    redirect_uri = build_local_redirect_uri()
    state = secrets.token_urlsafe(16)

    oauth = SoundCloudOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=redirect_uri,
    )

    auth_url = oauth.build_authorize_url(state)
    callback_server = OAuthCallbackServer(
        host=LOCAL_CALLBACK_HOST,
        port=LOCAL_CALLBACK_PORT,
        callback_path=LOCAL_CALLBACK_PATH,
    )

    callback_server.start()
    logging.info("FastAPI callback server started at %s", redirect_uri)
    return auth_url, callback_server, state, oauth

async def zxc(auth_url, callback_server, state, oauth):
    try:
        logging.info("Open this URL for authorization:\n%s", auth_url)
        if OPEN_AUTH_URL_IN_BROWSER:
            webbrowser.open(auth_url)

        result = callback_server.wait_for_callback(OAUTH_WAIT_TIMEOUT_SECONDS)
        if result is None:
            raise SoundCloudApiError("OAuth callback timeout")
        if result.get("error"):
            raise SoundCloudApiError(f"OAuth error: {result['error']}")
        if result.get("state") and result["state"] != state:
            raise SoundCloudApiError("OAuth state mismatch")

        code = result.get("code")
        if not code:
            raise SoundCloudApiError("OAuth callback has no code")

        token_data = await oauth.exchange_code_for_token(code)
        access_token = token_data.get("access_token")
        if not access_token:
            raise SoundCloudApiError(f"No access_token in response: {token_data}")

        logging.info("OAuth completed successfully")
        return str(access_token)
    finally:
        callback_server.stop()
        logging.info("FastAPI callback server stopped")

async def main() -> None:
    auth_url, callback_server, state, oauth = await authorize_and_get_token()
    while True:
        c = input("Enter command: ")
        match c:
            case 's':
                token = await zxc(auth_url, callback_server, state, oauth)
                print("ACCESS_TOKEN:", token)
            case 'w':
                print('sleeping 5s')
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())