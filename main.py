import asyncio
import logging
import os
import re
import sys

from services.ym_music import YandexMusic
from loguru import logger
from typing import List, Dict, Optional

from config import *


def color_formatter(record):
	message = record["message"].replace("{", "{{").replace("}", "}}")
	state = record["extra"].get("state", None)
	end = record["extra"].get("end", '\n')

	if re.search(r'\[\+\]', message):
		message = message.replace('[+]', f'<green>[{state+"|" if state else ""}+]</green>')
	if re.search(r'\[\-\]', message):
		message = message.replace('[-]', f'<red>[{state+"|" if state else ""}-]</red>')
	if re.search(r'\[\!\]', message):
		message = message.replace('[!]', f'<yellow>[{state+"|" if state else ""}!]</yellow>')
	if re.search(r'\[\*\]', message):
		message = message.replace('[*]', f'<cyan>[{state+"|" if state else ""}*]</cyan>')
	if re.search(r'\[\+\+\]', message):
		message = message.replace('[++]', f'<cyan>[{state+"|" if state else ""}+]</cyan>')

	return f"{message}{end}"

logger.remove()

logger.add(
	sys.stdout,
	format=color_formatter,
	level="INFO",
	colorize=True
)

logger.add(
	"requests.log",
	format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
	level="DEBUG",
	encoding="utf-8",
	rotation="50 MB",
	retention="7 days",
)




class ShpotiMusicTool:
	def __init__(self):
		self.services = {
			'yandex_music': (True, 'Яндекс музыка'),
			'youtube_music': (False, 'YouTube Music'),
			'spotify': (False, 'Spotify'),
			'soudcloud': (True, 'SoundCloud'),
		}
		self.available_services = {
			k: v[1] for k, v in self.services.items() if v[0]
		}

		self.selected_import_service = None
		self.selected_import_service_token = None
		self.selected_export_service = None
		self.selected_export_service_token = None

	def select_import_service(self):
		last_error = None

		while True:
			os.system('cls' if os.name == 'nt' else 'clear')
			import_service_text = '\n'.join([f'{i}. [{"+" if i == (self.selected_import_service[0] if self.selected_import_service else None) else "-"}] {v}' for i, (k, v) in enumerate(self.available_services.items(), start=1)])
			err_msg = f'\n[!] {last_error}\n' if last_error else ''
			logger.info(import_service_text+'\n\n'+err_msg)
			last_error = None

			logger.info('<bold>[1]</bold> Выберите сервис из которого хотите перенести плейлисты: ', end='')
			this_selected_import_service = input().lower()
			try:
				this_selected_import_service = int(this_selected_import_service)
				if this_selected_import_service > len(self.available_services):
					last_error = f'Номер сервиса не должен быть больше {len(self.available_services)}'
					continue
				elif this_selected_import_service <= 0:
					last_error = f'Номер сервиса не должен быть меньше 0'
					continue
				self.selected_import_service = (list(self.available_services.items())[this_selected_import_service-1], this_selected_import_service)
				break
			except Exception as e:
				last_error = f'Нужно ввести цифру(номер) сервиса ({e})'
			os.system('cls' if os.name == 'nt' else 'clear')

	def input_import_service_token(self):
		last_error = None

		while True:
			os.system('cls' if os.name == 'nt' else 'clear')
			selected_import_service_text = f'<green>[*]</green> Сервис для экспорта: <bold>{self.selected_import_service[0][1]}</bold>'
			input_token_text = ''
			err_msg = f'\n[!] {last_error}\n' if last_error else ''
			logger.info(selected_import_service_text+'\n\n'+input_token_text+'\n\n'+err_msg)



	def select_export_service(self):
		last_error = None

		while True:
			os.system('cls' if os.name == 'nt' else 'clear')
			selected_import_service_text = f'<green>[*]</green> Сервис для экспорта: <bold>{self.selected_import_service[0][1]}</bold>'
			export_service_text = '\n'.join([f'{i}. [{"+" if i == (self.selected_export_service[0] if self.selected_export_service else None) else "++" if i == self.selected_import_service[1] else "-"}] {v}' for i, (k, v) in enumerate(self.available_services.items(), start=1)])
			err_msg = f'\n[!] {last_error}\n' if last_error else ''
			logger.info(selected_import_service_text+'\n\n'+export_service_text+'\n\n'+err_msg)
			last_error = None


			logger.info('<bold>[2]</bold> Выберите сервис в который хотите перенести плейлисты: ', end='')
			this_selected_export_service = input().lower()
			try:
				this_selected_export_service = int(this_selected_export_service)
				if this_selected_export_service > len(self.available_services):
					last_error = f'Номер сервиса не должен быть больше {len(self.available_services)}'
					continue
				elif this_selected_export_service <= 0:
					last_error = f'Номер сервиса не должен быть меньше 0'
					continue
				self.selected_export_service = (list(self.available_services.items())[this_selected_export_service-1], this_selected_export_service)
				if this_selected_export_service == self.selected_import_service[1]:
					logger.info('[!] Вы выбрали 2 одинаковых сервиса, продолжить? [y-Да/N-Нет] > ', end='')
					r = input()
					if r.lower() == 'y':
						break
					else:
						self.selected_export_service = None
						continue
				break
			except Exception as e:
				last_error = f'Нужно ввести цифру(номер) сервиса ({e})'
			os.system('cls' if os.name == 'nt' else 'clear')


	def select_playlists_to_export(self, all_playlists: Dict[str, List]):
		selected_playlists = {i: item for i, item in enumerate(all_playlists.items(), start=1)}
		max_playlist_title = len(max(all_playlists.keys(), key=len))
		last_error = None

		while True:
			os.system('cls' if os.name == 'nt' else 'clear')
			selected_import_export_services_text = f'<green>[*]</green> Сервис для экспорта: <bold>{self.selected_import_service[0][1]}</bold>\n<green>[*]</green> Сервис для импорта: <bold>{self.selected_export_service[0][1]}</bold>\n\n{"="*(max_playlist_title+24)}\n'
			playlists_text = '\n'.join([f'{i}. [{"+" if i in selected_playlists else "-"}] {k:<{max_playlist_title}} | Треков: <cyan>{len(v)}</cyan>' for i, (k, v) in enumerate(all_playlists.items(), start=1)])
			err_msg = f'\n[!] {last_error}\n' if last_error else ''
			logger.info(selected_import_export_services_text+'\n\n'+playlists_text+'\n\n'+err_msg+'\n[!] Для продолжения - введите "<green>Y</green>" (без кавычек)\n')
			last_error = None

			logger.info('<bold>[3]</bold> Выберите какие плейлисты нужно перенести: ', end='')
			selected_playlist = input().lower()
			if selected_playlist == 'y':
				break
			try:
				selected_playlist = int(selected_playlist)
				if selected_playlist > len(all_playlists):
					last_error = f'Номер плейлиста не должен быть больше {len(all_playlists)}'
					continue
				elif selected_playlist <= 0:
					last_error = f'Номер плейлиста не должен быть меньше 0'
					continue
				if selected_playlist in selected_playlists:
					del selected_playlists[selected_playlist]
				else:
					selected_playlists[selected_playlist] = list(all_playlists.items())[selected_playlist-1]
			except Exception as e:
				last_error = f'Нужно ввести цифру(номер) плейлиста ({e})'
			os.system('cls' if os.name == 'nt' else 'clear')


def main():
	z = ShpotiMusicTool()
	z.select_import_service()
	z.select_export_service()

	os.system('cls' if os.name == 'nt' else 'clear')
	logger.info('[*] Parsing playlists and tracks...')
	if z.selected_import_service[0][0] == 'yandex_music':
		ymc = YandexMusic(YANDEX_TOKEN)
		all_playlists = ymc.get_all_playlists()
	else:
		logger.error('[-] Invalid service')
		exit(0)

	if len(all_playlists) == 0:
		logger.info('[-] Empty playlists')
		exit()

	z.select_playlists_to_export(all_playlists)


if __name__ == "__main__":
	main()