import json
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


# =========================
# USER SETTINGS (EDIT HERE)
# =========================
CLIENT_ID = "cIYxtC61UuswkJN1H7looUKPUL3beAqj"
CLIENT_SECRET = "nyHItX1eTNfC8TpjhhVFstmo0ia4dwpU"
REDIRECT_URI = "https://t.me/LUCKYBANANA5894"
PUBLIC_CLIENT_ID = "1IzwHiVxAHeYKAMqN0IIGD3ZARgJy2kl"

# After first OAuth step, paste token here.
ACCESS_TOKEN = "eyJraWQiOiJzYy13dVlRRjRjIiwidHlwIjoiYXQrSldUIiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiJzb3VuZGNsb3VkOnVzZXJzOjE0Mjg1OTg2MDgiLCJhdWQiOiJodHRwczovL3NvdW5kY2xvdWQuY29tIiwic2NvcGUiOiIiLCJpc3MiOiJodHRwczovL3NlY3VyZS5zb3VuZGNsb3VkLmNvbSIsImNhaSI6IjMyNzIzMCIsImV4cCI6MTc3MjU0MjM4NiwiaWF0IjoxNzcyNTM4Nzg2LCJqdGkiOiI3NDYwYTUxMi1lZjI2LTRhZTAtOTE5Yi1kMzc5M2I0NTM3YTEiLCJjbGllbnRfaWQiOiJjSVl4dEM2MVV1c3drSk4xSDdsb29VS1BVTDNiZUFxaiIsInNpZCI6IjAxS0pTUlBXVk1FQTZFSDY5UlhZNVRBQUpBIn0.apnKs908hV1vgp_gyFBiJ5IsZnJA2DYbhnBK4GX_CIc1NrczLVEpefKBHobYBCmixrzkiQ4na3ukuVlXDX311W_wy70iT-0hSLVWpzReywUynVHuPnGKcyEe9YsS5DUPL1XtMyYCSvxBP2ZVYGhyP7h0n6Epq79D-VcpYjHyOmJRq9KgDz6hd2gzmIzhWOH7iIhZWVjIcGXeOXTdMs8YSUgxtR7ulzxakH36utERJGSY-F3BCeb27Eh9QK_hXNV3DUuDGhgAsREM7soZKo-yNm1cxxgOl8VigWXu2lHBZpR61-zSvrqsXh7RT8ZLJrMwpKcIIwRLoxTLNv36mA9K-Q"

# Modes: "authorize", "search", "create", "add", "create_from_names", "me"
MODE = "create"

# For MODE="search"
SEARCH_QUERY = "Ivoxygen "
SEARCH_LIMIT = 10

# For MODE="create"
PLAYLIST_TITLE = "My Playlist"
PLAYLIST_DESCRIPTION = "Created via raw SoundCloud API"
PLAYLIST_PUBLIC = False
CREATE_TRACK_IDS: List[int] = [
    254111917,
    254112221,
    254111788
]

# For MODE="add"
PLAYLIST_ID_TO_UPDATE = 0
TRACK_IDS_TO_ADD: List[int] = [
    1650727722,
    1858590672,
    2080104336,
    1933341872,
    2185252199
]

# For MODE="create_from_names"
AUTO_PLAYLIST_TITLE = "Auto Playlist"
AUTO_PLAYLIST_PUBLIC = False
TRACK_NAMES: List[str] = [
    "Daft Punk One More Time",
    "The Weeknd Blinding Lights",
]


class SoundCloudApiError(RuntimeError):
    pass


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
                "tracks": [{"id": int(track_id)} for track_id in (track_ids or [])],
            }
        }
        return self._request(
            "POST",
            f"/playlists",
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
                "tracks": [{"id": int(track_id)} for track_id in track_ids],
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


def mode_authorize() -> None:
    oauth = SoundCloudOAuth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
    state = secrets.token_urlsafe(16)
    url = oauth.build_authorize_url(state)

    print("1) Open this URL in browser and allow access:")
    print(url)
    print("\n2) Copy `code` from redirect URL and paste below.")
    print("   Redirect example: https://your-redirect?code=...&state=...")

    code = input("\nPaste code here: ").strip()
    if not code:
        raise SoundCloudApiError("No code provided")

    token_data = oauth.exchange_code_for_token(code)
    access_token = token_data.get("access_token", "")

    print("\nOAuth response:")
    print(json.dumps(token_data, ensure_ascii=False, indent=2))
    if access_token:
        print("\nPaste this into ACCESS_TOKEN in script:")
        print(access_token)


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

        if mode == "authorize":
            mode_authorize()
            return 0

        api = SoundCloudAPI(
            access_token=ACCESS_TOKEN or None,
            client_id=CLIENT_ID,
            public_client_id=PUBLIC_CLIENT_ID,
        )

        if mode in {"me", "create", "add", "create_from_names"} and not ACCESS_TOKEN:
            raise SoundCloudApiError("Set ACCESS_TOKEN in script or use MODE='authorize' first")

        if mode == "search":
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
