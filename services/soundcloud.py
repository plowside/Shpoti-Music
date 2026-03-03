import async_tls_client
import asyncio
import json
import logging

from typing import List, Dict, Optional, Any
from urllib.parse import urlparse

from frida_tools.application import await_enter

logging.basicConfig(level=logging.DEBUG)

class User:
    def __init__(self, data: dict, sc: "SoundCloud" = None):
        self._data = data or {}
        self._sc = sc if sc else SoundCloud()

        for k, v in self._data.items():
            setattr(self, k, v)

    def to_dict(self):
        return dict(self._data)

    async def get_playlists(self, limit: int = 200):
        playlists = await self._sc.get_user_playlists(self.id, limit=limit)
        return [Playlist(p, sc=self._sc) for p in playlists]


class Playlist:
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
    tracks: Optional[List[Dict[str, Any]]]
    track_count: Optional[int]

    def __init__(self, data: dict, sc: "SoundCloud" = None):
        self._data = data or {}
        self._sc = sc if sc else SoundCloud()

        for k, v in self._data.items():
            setattr(self, k, v)

    def to_dict(self):
        return dict(self._data)

    async def refresh(self):
        data = await self._sc.get_playlist(self.id)
        self._data = data or {}
        for k, v in self._data.items():
            setattr(self, k, v)
        return self

    async def get_tracks(self, fetch_full_info: bool = True):
        if fetch_full_info:
            tracks = await self._sc.get_tracks_batch([str(t['id']) for t in self.tracks])
        else:
            tracks = self.tracks
        return [Track(t, sc=self._sc) for t in tracks]


class Track:
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
    user: Optional[Dict[str, Any]]
    title_formated: Optional[str]

    def __init__(self, data: dict, sc: "SoundCloud" = None):
        self._data = data or {}
        self._sc = sc if sc else SoundCloud()

        for k, v in self._data.items():
            setattr(self, k, v)

    def to_dict(self):
        return dict(self._data)

    async def refresh(self):
        data = await self._sc.get_track(self.id)
        self._data = data or {}
        for k, v in self._data.items():
            setattr(self, k, v)
        return self



class SoundCloud:
    def __init__(self):
        self.session = async_tls_client.AsyncSession(random_tls_extension_order=True)
        self.soundcloud_domain = 'soundcloud.com'
        self.client_id = '1IzwHiVxAHeYKAMqN0IIGD3ZARgJy2kl'
        self.RESOLVE_URL = 'https://api-v2.soundcloud.com/resolve?url={url}&client_id={client_id}'
        self.USER_PLAYLISTS_URL = 'https://api-v2.soundcloud.com/users/{user_id}/playlists_without_albums'
        self.PLAYLIST_URL = 'https://api-v2.soundcloud.com/playlists/{playlist_id}'
        self.TRACK_URL = 'https://api-v2.soundcloud.com/tracks/{track_id}'
        self.TRACKS_BATCH_URL = 'https://api-v2.soundcloud.com/tracks?ids={tracks_ids}&client_id={client_id}'

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

    async def resolve(self, url: str):
        if urlparse(url).netloc != self.soundcloud_domain:
            url = await self.follow_url(url)
            if not url:
                raise ValueError(f'Not soundcloud domain: {url}')
        req = await self.session.get(self.RESOLVE_URL.format(url=url, client_id=self.client_id), headers=self.headers)
        req_json = req.json()
        kind = req_json['kind'] # user | playlist | system-playlist | track
        logging.info(f'[+] Resolved {kind}')
        if kind == 'user':
            return self.user_from(req_json)
        elif kind in ('playlist', 'system-playlist'):
            return self.playlist_from(req_json)
        elif kind == 'track':
            return self.track_from(req_json)
        return req_json

    def user_from(self, data: dict):
        return User(data, sc=self)

    def playlist_from(self, data: dict):
        return Playlist(data, sc=self)

    def track_from(self, data: dict):
        return Track(data, sc=self)

    async def follow_url(self, url: str):
        try:
            logging.info(f'Requesting {url}')
            req = await self.session.get(url, headers=self.headers, allow_redirects=True)
            if urlparse(req.url).netloc != self.soundcloud_domain:
                logging.info(f'Request followed to unknown url: {req.url}')
                return None
            logging.info(f'Request followed to soundcloud url: {req.url}')
            return req.url
        except Exception as e:
            logging.error(f'Error on follow {url}: {e}')
            return None

    async def get_user_playlists(self, user_id: int, limit: int = 200):
        params = {
            'client_id': self.client_id,
            'limit': str(limit),
            'offset': '0',
            'linked_partitioning': '1',
        }
        all_items = []
        while True:
            req = await self.session.get(self.USER_PLAYLISTS_URL.format(user_id=user_id), headers=self.headers, params=params)
            data = req.json()
            collection = data.get('collection') or []
            all_items.extend(collection)
            next_href = data.get('next_href')
            if not next_href:
                break
            url = next_href
            params = None
        return all_items

    async def get_playlist(self, playlist_id: int):
        params = {'client_id': self.client_id}
        url = self.PLAYLIST_URL.format(playlist_id=playlist_id)
        req = await self.session.get(url, headers=self.headers, params=params)
        return req.json()

    async def get_track(self, track_id: int | list):
        if isinstance(track_id, list):
            return await self.get_tracks_batch(track_id)
        req = await self.session.get(self.TRACK_URL.format(track_id=track_id), headers=self.headers, params={'client_id': self.client_id})
        return req.json()

    async def _fetch_tracks_batch(self, batch_ids: List[str]):
        batch = ','.join(batch_ids)
        req = await self.session.get(
            self.TRACKS_BATCH_URL.format(tracks_ids=batch, client_id=self.client_id),
            headers=self.headers,
        )
        tracks = []
        for t in req.json().copy():
            if '-' not in t['title']: #t.get('user', {}).get('verified', False):
                publisher_metadata = t.get('publisher_metadata', {})
                artist = publisher_metadata.get('artist', None) if publisher_metadata else None
                if not artist:
                    artist = t.get('user', {}).get('username', None)
            else:
                artist = None
            t['title_formated'] = f"{t['title']}{' - '+artist if artist else ''}"
            tracks.append(t)
        return tracks

    async def get_tracks_batch(self, tracks_ids: list):
        batch_size = 50
        if not isinstance(tracks_ids, list):
            tracks_ids = [tracks_ids]
        tracks_ids = [str(t) for t in tracks_ids]

        batches = [tracks_ids[i:i + batch_size] for i in range(0, len(tracks_ids), batch_size)]
        tasks = [asyncio.create_task(self._fetch_tracks_batch(b)) for b in batches]
        results = await asyncio.gather(*tasks)

        tracks: List[dict] = []
        for chunk in results:
            tracks.extend(chunk)
        return tracks
