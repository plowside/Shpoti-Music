from __future__ import annotations

import async_tls_client
import tls_client
import asyncio
import logging

from async_tls_client.response import Response
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse


class _SCModel:
    def __init__(self, data: dict, sc: "SoundCloud" = None):
        self._data = data or {}
        self._sc = sc if sc else SoundCloud()
        self._bind_data()

    def _bind_data(self):
        for key, value in self._data.items():
            setattr(self, key, value)

    def to_dict(self):
        return dict(self._data)


class User(_SCModel):
    avatar_url: Optional[str]
    city: Optional[str]
    comments_count: Optional[int]
    country_code: Optional[str]
    created_at: Optional[str]
    creator_subscriptions: Optional[list]
    creator_subscription: Optional[Dict[str, Any]]
    description: Optional[str]
    followers_count: Optional[int]
    followings_count: Optional[int]
    first_name: Optional[str]
    full_name: Optional[str]
    groups_count: Optional[int]
    id: Optional[int]
    kind: Optional[str]
    last_modified: Optional[str]
    last_name: Optional[str]
    likes_count: Optional[int]
    playlist_likes_count: Optional[int]
    permalink: Optional[str]
    permalink_url: Optional[str]
    playlist_count: Optional[int]
    reposts_count: Optional[int]
    track_count: Optional[int]
    uri: Optional[str]
    urn: Optional[str]
    username: Optional[str]
    verified: Optional[bool]
    visuals: Optional[Dict[str, Any]]
    badges: Optional[Dict[str, Any]]
    station_urn: Optional[str]
    station_permalink: Optional[str]
    date_of_birth: Optional[str]

    async def get_playlists(self, limit: int = 200) -> List[Playlist]:
        playlists = await self._sc.get_user_playlists(self.id, limit=limit, return_dict_obj=True)
        return [Playlist(p, sc=self._sc) for p in playlists]


class Playlist(_SCModel):
    artwork_url: Optional[str]
    created_at: Optional[str]
    description: Optional[str]
    duration: Optional[int]
    embeddable_by: Optional[str]
    genre: Optional[str]
    id: Optional[int]
    kind: Optional[str]
    label_name: Optional[str]
    last_modified: Optional[str]
    license: Optional[str]
    likes_count: Optional[int]
    managed_by_feeds: Optional[bool]
    permalink: Optional[str]
    permalink_url: Optional[str]
    public: Optional[bool]
    purchase_title: Optional[str]
    purchase_url: Optional[str]
    release_date: Optional[str]
    reposts_count: Optional[int]
    secret_token: Optional[str]
    sharing: Optional[str]
    tag_list: Optional[str]
    title: Optional[str]
    uri: Optional[str]
    user_id: Optional[int]
    set_type: Optional[str]
    is_album: Optional[bool]
    published_at: Optional[str]
    display_date: Optional[str]
    user: Optional[Dict[str, Any]]
    tracks: Optional[List[Track]]
    track_count: Optional[int]

    def __init__(self, data: dict, sc: "SoundCloud" = None):
        super().__init__(data=data, sc=sc)

        if hasattr(self, 'tracks'):
            self.tracks = [Track(t, sc=sc) for t in self.tracks]

    async def refresh(self):
        data = await self._sc.get_playlist(self.id, return_dict_obj=True)
        self._data = data or {}
        self._bind_data()
        return self

    async def get_tracks(self, fetch_full_info: bool = True):
        if fetch_full_info:
            tracks = await self._sc.get_tracks([str(t.id) for t in self.tracks], return_dict_obj=True)
        else:
            tracks = self.tracks
        return [Track(t, sc=self._sc) for t in tracks]

    async def delete(self):
        resp = await self._sc.delete_playlist(self.id)
        return True if resp.get('status', '') == '200 - OK' else False


class Track(_SCModel):
    artwork_url: Optional[str]
    caption: Optional[str]
    commentable: Optional[bool]
    comment_count: Optional[int]
    created_at: Optional[str]
    description: Optional[str]
    downloadable: Optional[bool]
    download_count: Optional[int]
    duration: Optional[int]
    full_duration: Optional[int]
    embeddable_by: Optional[str]
    genre: Optional[str]
    has_downloads_left: Optional[bool]
    id: Optional[int]
    kind: Optional[str]
    label_name: Optional[str]
    last_modified: Optional[str]
    license: Optional[str]
    likes_count: Optional[int]
    permalink: Optional[str]
    permalink_url: Optional[str]
    playback_count: Optional[int]
    public: Optional[bool]
    publisher_metadata: Optional[Dict[str, Any]]
    purchase_title: Optional[str]
    purchase_url: Optional[str]
    release_date: Optional[str]
    reposts_count: Optional[int]
    secret_token: Optional[str]
    sharing: Optional[str]
    state: Optional[str]
    streamable: Optional[bool]
    tag_list: Optional[str]
    title: Optional[str]
    uri: Optional[str]
    urn: Optional[str]
    user_id: Optional[int]
    visuals: Optional[str]
    waveform_url: Optional[str]
    display_date: Optional[str]
    media: Optional[Dict[str, Any]]
    station_urn: Optional[str]
    station_permalink: Optional[str]
    track_authorization: Optional[str]
    monetization_model: Optional[str]
    policy: Optional[str]
    user: Optional[User | Dict[str, Any]]
    title_formated: Optional[str]

    def __init__(self, data: dict, sc: "SoundCloud" = None):
        super().__init__(data=data, sc=sc)

        if hasattr(self, 'user'):
            self.user = User(self.user, sc=self._sc)

            artist = None
            if '-' not in str(self.title):
                try:
                    publisher_metadata = self.publisher_metadata or {}
                except:
                    publisher_metadata = {}
                artist = publisher_metadata.get('artist', None) if publisher_metadata else None
                if not artist and self.user:
                    artist = self.user.username

            self.title_formated = f"{self.title}{' - ' + artist if artist else ''}"

    async def refresh(self):
        data = await self._sc.get_track(self.id)
        self._data = data or {}
        self._bind_data()
        return self


class SoundCloud:
    def __init__(self, client_id: str = None, client_secret: str = None, redirect_uri: str = None, access_token: str = None):
        self.session = async_tls_client.AsyncSession(random_tls_extension_order=True)
        self.SOUNDCLOUD_DOMAIN = 'soundcloud.com'
        self.SOUNDCLOUD_API = f'api.{self.SOUNDCLOUD_DOMAIN}'
        self.SOUNDCLOUD_PUBLIC_API = f'api-v2.{self.SOUNDCLOUD_DOMAIN}'
        self.RESOLVE_URL = '/resolve?url={url}&client_id={client_id}'
        self.USER_PLAYLISTS_URL = '/users/{user_id}/playlists_without_albums'
        self.PLAYLIST_URL = '/playlists/{playlist_id}'
        self.TRACK_URL = '/tracks/{track_id}'
        self.TRACKS_BATCH_URL = '/tracks?ids={track_ids}&client_id={client_id}'

        # AUTH PART
        self.client_id_public = '1IzwHiVxAHeYKAMqN0IIGD3ZARgJy2kl'
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = access_token
        if self.client_id and self.client_secret and self.redirect_uri and not self.access_token:
            result = self.auth(self.client_id, self.client_secret, self.redirect_uri)
            if not result:
                logging.info('SoundCloud Auth failed, private requests are not available')

        self.headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.1',
            'Accept-Language': 'ru,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Origin': 'https://soundcloud.com',
            'Pragma': 'no-cache',
            'Referer': 'https://soundcloud.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

    def user_from(self, data: dict):
        return User(data, sc=self)

    def playlist_from(self, data: dict):
        return Playlist(data, sc=self)

    def track_from(self, data: dict):
        return Track(data, sc=self)

    def auth(self, client_id, client_secret, redirect_uri):
        while True:
            try:
                result = authorize_and_get_token(client_id, client_secret, redirect_uri)
                self.access_token = result
                logging.info(f'Auth successful for client_id: {client_id} | Token: {self.access_token}')
                return True
            except Exception as e:
                logging.error(f'Error on auth: {e}')
                continue
        self.client_id = None
        self.client_secret = None
        self.redirect_uri = None
        self.access_token = None
        return False


    async def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, payload: Optional[Dict[str, Any] | str] = None, use_auth: bool = False, allow_redirects: bool = True, return_req_obj: bool = False) -> Dict[str, Any] | Response | None:
        headers = self.headers.copy()
        if use_auth:
            if not self.access_token:
                raise ValueError('ACCESS_TOKEN is required for this request')
            headers['Authorization'] = f'OAuth {self.access_token}'
        try:
            url = f'https://{self.SOUNDCLOUD_API if use_auth else self.SOUNDCLOUD_PUBLIC_API}{path}' if not path.startswith('http') else path
            req = await self.session.execute_request(
                url=url, params=params, headers=headers, method=method.upper(), allow_redirects=allow_redirects,
                **{'json' if isinstance(payload, dict) else 'data': payload})
            if req.status_code == 401:
                logging.error(f'[resp.code=401] Unauthorized access to {path}')
            elif req.status_code == 403:
                logging.error(f'[resp.code=403] Forbidden access to {path}')
            return req if return_req_obj else req.json()
        except Exception as e:
            logging.error(f'Error on request {path}: {e}')
            return None

    async def resolve(self, url: str) -> User | Playlist | Track | dict | None:
        if urlparse(url).netloc != self.SOUNDCLOUD_DOMAIN:
            url = await self.follow_url(url)
            if not url:
                raise ValueError(f'Not soundcloud domain: {url}')
        resp = await self._request('GET', self.RESOLVE_URL.format(url=url, client_id=self.client_id_public))
        kind = resp['kind']
        logging.info(f'[+] Resolved {kind}')
        parsers = {
            'user': self.user_from,
            'playlist': self.playlist_from,
            'system-playlist': self.playlist_from,
            'track': self.track_from,
        }
        parser = parsers.get(kind)
        if parser:
            return parser(resp)
        return resp

    async def follow_url(self, url: str) -> str | None:
        try:
            logging.info(f'Requesting {url}')
            req = await self._request('GET', url, allow_redirects=True, return_req_obj=True)
            if urlparse(req.url).netloc != self.SOUNDCLOUD_DOMAIN:
                logging.info(f'Request followed to unknown url: {req.url}')
                return None
            logging.info(f'Request followed to soundcloud url: {req.url}')
            return req.url
        except Exception as e:
            logging.error(f'Error on follow {url}: {e}')
            return None

    async def get_user_playlists(self, user_id: int, limit: int = 200, return_dict_obj: bool = False) ->  List[Dict[str, Any]] | List[Playlist]:
        params = {
            'client_id': self.client_id_public,
            'limit': str(limit),
            'offset': '0',
            'linked_partitioning': '1',
        }
        url = self.USER_PLAYLISTS_URL.format(user_id=user_id)
        all_items = []
        while True:
            resp = await self._request('GET', url, params=params)
            collection = resp.get('collection') or []
            all_items.extend(collection if return_dict_obj or not collection else Playlist(collection))
            next_href = resp.get('next_href')
            if not next_href:
                break
            url = next_href
            params = None
        return all_items

    async def get_track(self, track_id: int, return_dict_obj: bool = False) -> Dict[str, Any]:
        track = await self._request('GET',
            self.TRACK_URL.format(track_id=track_id),
            params={'client_id': self.client_id_public},
        )
        return self._format_track_title(track) if return_dict_obj else Track(track, sc=self)

    async def get_tracks(self, track_ids: list, return_dict_obj: bool = False) -> List[dict]:
        batch_size = 50
        if not isinstance(track_ids, list):
            track_ids = [track_ids]
        track_ids = [str(t) for t in track_ids]

        batches = [track_ids[i:i + batch_size] for i in range(0, len(track_ids), batch_size)]
        tasks = [asyncio.create_task(self._fetch_tracks_batch(b)) for b in batches]
        results = await asyncio.gather(*tasks)

        tracks: List[dict] = []
        for this_tracks in results:
            tracks.extend(this_tracks if return_dict_obj else [Track(t, sc=self) for t in this_tracks])
        return tracks

    async def _fetch_tracks_batch(self, batch_ids: List[str]) -> List[Track]:
        batch = ','.join(batch_ids)
        resp = await self._request('GET',
            self.TRACKS_BATCH_URL.format(track_ids=batch, client_id=self.client_id_public),
        )
        tracks = []
        for track in resp:
            tracks.append(self._format_track_title(track))
        return tracks

    async def search_track(self, query: str, limit: int = 10, best_matches: bool = True, policy: str = 'ALLOW') -> List[Track]:
        resp = await self._request(
            'GET',
            '/search/tracks',
            params={'q': query, 'limit': str(limit), 'offset': 0, 'linked_partitioning': 1, 'client_id': self.client_id_public},
            use_auth=False
        )
        tracks = resp.get('collection')
        result = []
        if best_matches:
            for t in tracks:
                t = self._format_track_title(t)
                found_shit = [x in t['title_formated'].lower() for x in ['slowed', 'sped up', 'speed up', 'daycore', 'nightcore', 'mashup', 'remix'] if x is True]

        else:
            result = [Track(t) for t in tracks if (t.get('policy', None) == policy if isinstance(policy, str) else True)] or []
        return result

    async def search_tracks(self, track_names: list[str], add_matches: int = 1, return_dict_obj: bool = False) -> List[dict]:
        if not isinstance(track_names, list):
            track_names = [track_names]

        tasks = [asyncio.create_task(self.search_track(t, limit=10)) for t in track_names]
        results = await asyncio.gather(*tasks)

        tracks: List[dict] = []
        for this_tracks in results:
            tracks.extend(this_tracks if return_dict_obj else this_tracks[:add_matches])
        return tracks

    async def get_me(self):
        resp = await self._request('GET', '/me', use_auth=True)
        return User(resp, sc=self)

    async def get_playlist(self, playlist_id: int, return_dict_obj: bool = False) -> Playlist | Dict[str, Any]:
        resp = await self._request('GET',
            self.PLAYLIST_URL.format(playlist_id=playlist_id),
            params={'client_id': self.client_id_public}
        )
        return resp if return_dict_obj else Playlist(resp, sc=self)

    async def create_playlist(self, title: str, description: str = None, track_ids: list = None, public: bool = True, return_dict_obj: bool = False) -> Playlist | Dict[str, Any]:
        payload = {
            'playlist': {
                'title': title,
                'description': description,
                'public': public,
                'tracks': [{'id': str(track_id)} for track_id in (track_ids or [])],
            }
        }

        resp = await self._request('POST', '/playlists', payload=payload, use_auth=True)
        return resp if return_dict_obj else Playlist(resp, sc=self)

    async def update_playlist_tracks(self, playlist_id: int, track_ids: list, return_dict_obj: bool = False) -> Playlist | Dict[str, Any]:
        payload = {
            'playlist': {
                'tracks': [{'id': str(track_id)} for track_id in track_ids]
            }
        }
        resp = await self._request(
            'PUT',
            f'/playlists/{playlist_id}',
            payload=payload,
            use_auth=True,
        )
        return resp if return_dict_obj else Playlist(resp, sc=self)

    async def add_tracks_to_playlist(self, playlist_id: int, new_track_ids: list, return_dict_obj: bool = False) -> Playlist | Dict[str, Any]:
        playlist = await self.get_playlist(playlist_id)
        current = playlist.tracks
        current_ids = [t for t in current if isinstance(t, dict) and 'id' in t]

        final_playlist_tracks = current_ids[:]
        seen = set(current_ids)
        for track_id in new_track_ids:
            track_id = int(track_id)
            if track_id not in seen:
                final_playlist_tracks.append(track_id)
                seen.add(track_id)

        return await self.update_playlist_tracks(playlist_id, final_playlist_tracks)

    async def delete_playlist(self, playlist_id: int) -> Dict[str, Any]:
        resp = await self._request('DELETE', f'/playlists/{playlist_id}', use_auth=True)
        return resp


    @staticmethod
    def _format_track_title(track: dict) -> dict:
        artist = None
        if '-' not in track.get('title', ''):
            publisher_metadata = track.get('publisher_metadata', {})
            artist = publisher_metadata.get('artist', None) if publisher_metadata else None
            if not artist and track.get('user'):
                artist = track['user'].get('username', None)

        track['title_formated'] = f"{track.get('title', '')}{' - ' + artist if artist else ''}"
        return track





CLIENT_ID = "cIYxtC61UuswkJN1H7looUKPUL3beAqj"
CLIENT_SECRET = "nyHItX1eTNfC8TpjhhVFstmo0ia4dwpU"

LOCAL_CALLBACK_HOST = "127.0.0.1"
LOCAL_CALLBACK_PORT = 9067
LOCAL_CALLBACK_PATH = "/sc-callback"
OAUTH_WAIT_TIMEOUT_SECONDS = 180
OPEN_AUTH_URL_IN_BROWSER = True



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

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
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

        session = tls_client.Session(random_tls_extension_order=True)
        for token_url in self.TOKEN_URLS:
            try:
                resp = session.post(token_url, data=payload, headers=headers)
                body = resp.text
                if resp.status_code >= 400:
                    raise SoundCloudApiError(
                        f"Token endpoint {token_url} -> HTTP {resp.status_code}: {body}"
                    )
                return resp.json()
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

def authorize_and_get_token(client_id, client_secret, redirect_uri) -> str:
    state = secrets.token_urlsafe(16)

    oauth = SoundCloudOAuth(
        client_id=client_id,
        client_secret=client_secret,
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

        token_data = oauth.exchange_code_for_token(code)
        access_token = token_data.get("access_token")
        if not access_token:
            raise SoundCloudApiError(f"No access_token in response: {token_data}")

        logging.info("OAuth completed successfully")
        return str(access_token)
    finally:
        callback_server.stop()
        logging.info("FastAPI callback server stopped")