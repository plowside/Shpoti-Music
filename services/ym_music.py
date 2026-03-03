import logging
import yandex_music

from typing import List, Dict, Optional
from yandex_music import Playlist, TrackShort

from config import *

class YandexMusic:
	def __init__(self, yandex_token: str):
		self.yandex_token = yandex_token
		self.ym_client = yandex_music.Client(self.yandex_token)

	def get_all_playlists(self) -> Dict[str, List]:
		liked_tracks = self.get_liked_tracks()
		playlists = self.get_playlists()
		all_playlists = {'Мне нравится': liked_tracks, **playlists}
		return all_playlists

	def get_liked_tracks(self) -> List[Dict]:
		logging.info('Getting liked tracks from Yandex Music')
		liked_tracks = self.format_track(self.ym_client.users_likes_tracks().fetch_tracks())
		logging.info(f'Parsed {len(liked_tracks)} liked tracks')
		return liked_tracks

	def get_playlists(self) -> Dict[str, Dict]:
		logging.info('Getting playlists from Yandex Music')
		playlists = self.ym_client.users_playlists_list()
		tracks_by_playlist = {}
		for playlist in playlists:
			tracks_by_playlist[playlist.title] = self.format_track(playlist.fetch_tracks())
		logging.info(f'Parsed {len(tracks_by_playlist)} playlists and {len([z for x in (tracks_by_playlist.values()) for z in x])} tracks')
		return tracks_by_playlist

	def get_tracks(self, tracks):
		result_tracks = []
		for track in tracks:
			track = self.get_track(track)
			result_tracks.append(track)
		return result_tracks

	def get_track(self, track):
		track = track.fetch_track()
		track_data = self.format_track(track)
		return track_data

	def format_track(self, track):
		if isinstance(track, TrackShort):
			track = track.track
		if isinstance(track, list):
			tracks_data = []
			for track in track:
				if isinstance(track, TrackShort):
					track = track.track
				track_data = {
					'title': track.title,
					'artists': [artist.name for artist in track.artists],
					'album': track.albums[0].title if track.albums else 'Unknown',
					'year': track.albums[0].year if track.albums and track.albums[0].year else None,
					'duration': track.duration_ms,
					'id': track.id
				}
				track_data['title_formated'] = f"{track_data['title']} - {', '.join(track_data['artists'])}"
				tracks_data.append(track_data)
			return tracks_data
		else:
			track_data = {
				'title': track.title,
				'artists': [artist.name for artist in track.artists],
				'album': track.albums[0].title if track.albums else 'Unknown',
				'year': track.albums[0].year if track.albums and track.albums[0].year else None,
				'duration': track.duration_ms,
				'id': track.id
			}
			track_data['title_formated'] = f"{track_data['title']} - {', '.join(track_data['artists'])}"
			return track_data
