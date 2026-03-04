import json
import secrets
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional


# =========================
# USER SETTINGS (EDIT HERE)
# =========================
CLIENT_ID = "cIYxtC61UuswkJN1H7looUKPUL3beAqj"
CLIENT_SECRET = "nyHItX1eTNfC8TpjhhVFstmo0ia4dwpU"
PUBLIC_CLIENT_ID = "1IzwHiVxAHeYKAMqN0IIGD3ZARgJy2kl"

LOCAL_CALLBACK_HOST = "127.0.0.1"
LOCAL_CALLBACK_PORT = 9067
LOCAL_CALLBACK_PATH = "/callback"
OAUTH_WAIT_TIMEOUT_SECONDS = 180
OPEN_AUTH_URL_IN_BROWSER = True

# Modes: "authorize", "search", "create", "add", "create_from_names", "me"
MODE = "create_from_names"

# For MODE="search"
SEARCH_QUERY = "Ivoxygen new"
SEARCH_LIMIT = 10

# For MODE="create"
PLAYLIST_TITLE = "my playlist"
PLAYLIST_DESCRIPTION = "Created via SoundCloud API"
PLAYLIST_PUBLIC = True
CREATE_TRACK_IDS: List[int] = [
    306470944,
    2216251388,
    1191493201,
    2216330357,
    93331125,
]

# For MODE="add"
PLAYLIST_ID_TO_UPDATE = 0
TRACK_IDS_TO_ADD: List[int] = [
    1650727722,
    1858590672,
    2080104336,
    1933341872,
    2185252199,
]

# For MODE="create_from_names"
AUTO_PLAYLIST_TITLE = "Auto Playlist ZZZ"
AUTO_PLAYLIST_PUBLIC = True
TRACK_NAMES: List[str] = '''Cornfield Chase - Hans Zimmer
check - bbno$
СВЕТЛАНА! - NEXTIME
the prom - glaive
the girl next door - IVOXYGEN
Mutter - Rammstein
Resist and Disorder - Rezodrone, The Cartesian Duelists
Где мой дом? - IC3PEAK
попал - tewiq
Empathy - Crystal Castles
vertigo - rizza
Боль - quiizzzmeow, Мэйби Бэйби
мелатонин - плм
псы попадут в рай - плм
Cornfield Chase - Hans Zimmer'''.splitlines()


class SoundCloudApiError(RuntimeError):
    pass


class LocalOAuthCallbackServer:
    def __init__(self, host: str, port: int, callback_path: str) -> None:
        self.host = host
        self.port = port
        self.callback_path = callback_path
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._event = threading.Event()
        self._result: Dict[str, Optional[str]] = {"code": None, "state": None, "error": None}

    def _make_handler(self):
        parent = self

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path != parent.callback_path:
                    self.send_response(404)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"Not Found")
                    return

                params = urllib.parse.parse_qs(parsed.query)
                parent._result["code"] = (params.get("code") or [None])[0]
                parent._result["state"] = (params.get("state") or [None])[0]
                parent._result["error"] = (params.get("error") or [None])[0]
                parent._event.set()

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = (
                    "<html><body><h3>Authorization received.</h3>"
                    "<p>You can close this tab and return to the script.</p></body></html>"
                )
                self.wfile.write(html.encode("utf-8"))

            def log_message(self, format: str, *args: Any) -> None:
                return

        return CallbackHandler

    def __enter__(self) -> "LocalOAuthCallbackServer":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        if self._server is not None:
            return
        self._event.clear()
        self._result = {"code": None, "state": None, "error": None}
        handler = self._make_handler()
        self._server = ThreadingHTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._thread = None
        self._server = None

    def wait_for_result(self, timeout_seconds: int) -> Optional[Dict[str, Optional[str]]]:
        ok = self._event.wait(timeout=timeout_seconds)
        if not ok:
            return None
        return dict(self._result)


class SoundCloudOAuth:
    AUTH_URL = "https://secure.soundcloud.com/authorize"
    TOKEN_URLS = [
        "https://secure.soundcloud.com/oauth/token",
        "https://api.soundcloud.com/oauth2/token",
    ]

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

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        body = urllib.parse.urlencode(payload).encode("utf-8")

        last_error: Optional[Exception] = None
        for token_url in self.TOKEN_URLS:
            req = urllib.request.Request(
                token_url,
                data=body,
                method="POST",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw) if raw else {}
            except Exception as exc:
                last_error = exc

        raise SoundCloudApiError(f"OAuth token request failed: {last_error}")


def build_local_redirect_uri() -> str:
    return f"http://localhost:{LOCAL_CALLBACK_PORT}{LOCAL_CALLBACK_PATH}"


def authorize_and_get_token() -> str:
    redirect_uri = build_local_redirect_uri()
    oauth = SoundCloudOAuth(CLIENT_ID, CLIENT_SECRET, redirect_uri)
    state = secrets.token_urlsafe(16)
    auth_url = oauth.build_authorize_url(state)

    with LocalOAuthCallbackServer(LOCAL_CALLBACK_HOST, LOCAL_CALLBACK_PORT, LOCAL_CALLBACK_PATH) as server:
        print("Open authorization URL:")
        print(auth_url)
        if OPEN_AUTH_URL_IN_BROWSER:
            try:
                webbrowser.open(auth_url)
            except Exception:
                pass

        print(f"Waiting callback on {redirect_uri} ...")
        result = server.wait_for_result(OAUTH_WAIT_TIMEOUT_SECONDS)

    if result is None:
        raise SoundCloudApiError("OAuth callback timeout")
    if result.get("error"):
        raise SoundCloudApiError(f"OAuth error: {result['error']}")
    if result.get("state") and result["state"] != state:
        raise SoundCloudApiError("OAuth state mismatch")

    code = result.get("code") or ""
    if not code:
        raise SoundCloudApiError("No authorization code received")

    token_data = oauth.exchange_code_for_token(code)
    access_token = token_data.get("access_token") or ""
    if not access_token:
        raise SoundCloudApiError(f"OAuth response has no access_token: {token_data}")

    return access_token


class SoundCloudAPI:
    PUBLIC_BASE_URL = "https://api-v2.soundcloud.com"
    AUTH_BASE_URL = "https://api.soundcloud.com"

    def __init__(
        self,
        access_token: Optional[str],
        client_id: str,
        public_client_id: str,
        timeout: int = 30,
    ) -> None:
        if not client_id:
            raise ValueError("CLIENT_ID is required")
        if not public_client_id:
            raise ValueError("PUBLIC_CLIENT_ID is required")

        self.access_token = access_token
        self.client_id = client_id
        self.public_client_id = public_client_id
        self.timeout = timeout

    def _build_url(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
        include_client_id: bool = True,
        client_id_override: Optional[str] = None,
    ) -> str:
        query: Dict[str, Any] = {}
        if include_client_id:
            query["client_id"] = client_id_override or self.client_id
        if params:
            for key, value in params.items():
                if value is not None:
                    query[key] = value
        root = base_url or self.AUTH_BASE_URL
        if query:
            return f"{root}{path}?{urllib.parse.urlencode(query, doseq=True)}"
        return f"{root}{path}"

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        use_auth: bool = True,
        base_url: Optional[str] = None,
        include_client_id: bool = True,
        client_id_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = self._build_url(
            path,
            params=params,
            base_url=base_url,
            include_client_id=include_client_id,
            client_id_override=client_id_override,
        )

        raw_body = None
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        }
        if use_auth:
            if not self.access_token:
                raise SoundCloudApiError("ACCESS_TOKEN is required for this operation")
            headers["Authorization"] = f"OAuth {self.access_token}"

        if body is not None:
            raw_body = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url=url, data=raw_body, method=method.upper(), headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            raise SoundCloudApiError(f"HTTP {exc.code} {exc.reason} for {method} {path}: {err_body}") from exc
        except urllib.error.URLError as exc:
            raise SoundCloudApiError(f"Network error for {method} {path}: {exc}") from exc

    def get_me(self) -> Dict[str, Any]:
        return self._request("GET", "/me", use_auth=True, base_url=self.AUTH_BASE_URL, include_client_id=False)

    def search_tracks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        data = self._request(
            "GET",
            "/search/tracks",
            params={"q": query, "limit": int(limit), "offset": 0, "linked_partitioning": 1},
            use_auth=False,
            base_url=self.PUBLIC_BASE_URL,
            include_client_id=True,
            client_id_override=self.public_client_id,
        )
        collection = data.get("collection")
        return collection if isinstance(collection, list) else []

    def create_playlist(
        self,
        title: str,
        description: str,
        public: bool,
        track_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        body = {
            "playlist": {
                "title": title,
                "description": description,
                "sharing": "public" if public else "private",
                "tracks": [{"id": str(track_id)} for track_id in (track_ids or [])],
            }
        }
        return self._request(
            "POST",
            "/playlists",
            body=body,
            use_auth=True,
            base_url=self.AUTH_BASE_URL,
            include_client_id=False,
        )

    def get_playlist(self, playlist_id: int) -> Dict[str, Any]:
        return self._request(
            "GET",
            f"/playlists/{int(playlist_id)}",
            use_auth=True,
            base_url=self.AUTH_BASE_URL,
            include_client_id=False,
        )

    def update_playlist_tracks(self, playlist_id: int, track_ids: List[int]) -> Dict[str, Any]:
        body = {
            "playlist": {
                "tracks": [{"id": str(track_id)} for track_id in track_ids],
            }
        }
        return self._request(
            "PUT",
            f"/playlists/{int(playlist_id)}",
            body=body,
            use_auth=True,
            base_url=self.AUTH_BASE_URL,
            include_client_id=False,
        )

    def add_tracks_to_playlist(self, playlist_id: int, new_track_ids: List[int]) -> Dict[str, Any]:
        playlist = self.get_playlist(playlist_id)
        current = playlist.get("tracks") or []
        current_ids = [int(t["id"]) for t in current if isinstance(t, dict) and "id" in t]

        merged = current_ids[:]
        seen = set(current_ids)
        for track_id in new_track_ids:
            track_id = int(track_id)
            if track_id not in seen:
                merged.append(track_id)
                seen.add(track_id)

        return self.update_playlist_tracks(playlist_id, merged)


def print_track(track: Dict[str, Any]) -> None:
    track_id = track.get("id")
    title = track.get("title", "")
    artist = (track.get("user") or {}).get("username", "")
    print(f"{track_id}\t{title}\t{artist}")


def mode_search(api: SoundCloudAPI) -> None:
    tracks = api.search_tracks(SEARCH_QUERY, SEARCH_LIMIT)
    if not tracks:
        print("No tracks found")
        return
    for t in tracks:
        print_track(t)


def mode_create(api: SoundCloudAPI) -> None:
    playlist = api.create_playlist(
        title=PLAYLIST_TITLE,
        description=PLAYLIST_DESCRIPTION,
        public=PLAYLIST_PUBLIC,
        track_ids=CREATE_TRACK_IDS,
    )
    print(json.dumps({
        "id": playlist.get("id"),
        "title": playlist.get("title"),
        "permalink_url": playlist.get("permalink_url"),
    }, ensure_ascii=False, indent=2))


def mode_add(api: SoundCloudAPI) -> None:
    if not PLAYLIST_ID_TO_UPDATE:
        raise SoundCloudApiError("PLAYLIST_ID_TO_UPDATE is empty")
    if not TRACK_IDS_TO_ADD:
        raise SoundCloudApiError("TRACK_IDS_TO_ADD is empty")

    updated = api.add_tracks_to_playlist(PLAYLIST_ID_TO_UPDATE, TRACK_IDS_TO_ADD)
    print(json.dumps({
        "id": updated.get("id"),
        "title": updated.get("title"),
        "track_count": len(updated.get("tracks") or []),
        "permalink_url": updated.get("permalink_url"),
    }, ensure_ascii=False, indent=2))


def mode_create_from_names(api: SoundCloudAPI) -> None:
    if not TRACK_NAMES:
        raise SoundCloudApiError("TRACK_NAMES is empty")

    selected_ids: List[int] = []
    for name in TRACK_NAMES:
        found = api.search_tracks(name, limit=1)
        if not found:
            print(f"Not found: {name}")
            continue

        track = found[0]
        track_id = int(track["id"])
        selected_ids.append(track_id)
        print(f"Selected: {track_id}\t{track.get('title', '')}")

    playlist = api.create_playlist(
        title=AUTO_PLAYLIST_TITLE,
        description="Created from track names",
        public=AUTO_PLAYLIST_PUBLIC,
        track_ids=selected_ids,
    )
    print(json.dumps({
        "id": playlist.get("id"),
        "title": playlist.get("title"),
        "track_count": len(selected_ids),
        "permalink_url": playlist.get("permalink_url"),
    }, ensure_ascii=False, indent=2))


def mode_me(api: SoundCloudAPI) -> None:
    me = api.get_me()
    print(json.dumps({
        "id": me.get("id"),
        "username": me.get("username"),
        "permalink_url": me.get("permalink_url"),
    }, ensure_ascii=False, indent=2))


def main() -> int:
    try:
        mode = MODE.strip().lower()
        auth_required_modes = {"authorize", "me", "create", "add", "create_from_names"}

        access_token: Optional[str] = None
        if mode in auth_required_modes:
            access_token = authorize_and_get_token()
            print("OAuth authorization completed")

        api = SoundCloudAPI(
            access_token=access_token,
            client_id=CLIENT_ID,
            public_client_id=PUBLIC_CLIENT_ID,
        )

        if mode == "authorize":
            me = api.get_me()
            print(json.dumps({
                "id": me.get("id"),
                "username": me.get("username"),
            }, ensure_ascii=False, indent=2))
        elif mode == "search":
            mode_search(api)
        elif mode == "create":
            mode_create(api)
        elif mode == "add":
            mode_add(api)
        elif mode == "create_from_names":
            mode_create_from_names(api)
        elif mode == "me":
            mode_me(api)
        else:
            raise SoundCloudApiError(f"Unknown MODE: {MODE}")

        return 0
    except SoundCloudApiError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())