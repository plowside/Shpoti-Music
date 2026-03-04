import asyncio
import json

from services import soundcloud, ym_music
from services.soundcloud import Track
from config import *

###################### SOUNDCLOUD ######################
async def main():
    client_id = 'cIYxtC61UuswkJN1H7looUKPUL3beAqj'
    client_secret = 'nyHItX1eTNfC8TpjhhVFstmo0ia4dwpU'
    redirect_uri = 'http://localhost:9067/sc-callback'
    access_token = 'eyJraWQiOiJzYy13dVlRRjRjIiwidHlwIjoiYXQrSldUIiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiJzb3VuZGNsb3VkOnVzZXJzOjE0Mjg1OTg2MDgiLCJhdWQiOiJodHRwczovL3NvdW5kY2xvdWQuY29tIiwic2NvcGUiOiIiLCJpc3MiOiJodHRwczovL3NlY3VyZS5zb3VuZGNsb3VkLmNvbSIsImNhaSI6IjMyNzIzMCIsImV4cCI6MTc3MjU3NTgwOCwiaWF0IjoxNzcyNTcyMjA4LCJqdGkiOiI5YzY3ZjgyMC1lNDVlLTQ2YzAtOGVlZi1lYzFkYmM0ZDBmNzUiLCJjbGllbnRfaWQiOiJjSVl4dEM2MVV1c3drSk4xSDdsb29VS1BVTDNiZUFxaiIsInNpZCI6IjAxS0pUUkpWU1FFQ0dDTTVSTU1HMDNOVjREIn0.ZEJHcGgPajQNbMFVMt3FED3VM4gyYOh27Ret5839s6X50sELkzkUVOoyDqXxE7B-RPVwBHraU9jS10SFu1gQE7a2PgZ9pGqs1gUFqAI4Uno7mvw89hOrYerVm37bBHwE3alaSkaSywH_5MPpL8tsCnipE0fqVTf72XyFRZ9cO41AMdngkyqNIDFpZM6iGphYwtQtjxqXL36Iwbly-EYZMqaRhTQYN-JeLYRk0hmnDfWTqFJz4n-ZWWiygfhjv85W5pXBfDUGdwFV_hf7UR1b3nMN17MhtBhg5-4QhGDrhMnFHANXZPE6Ctj-7Njasw-9w9SGldrsQAdOKz1I_bVEZQ'
    sc = soundcloud.SoundCloud(client_id, client_secret, redirect_uri, access_token)
    r = await sc.search_track('keep up - odetari')
    for t in r:
        print(t.title_formated, '|', t.permalink_url)
    # print('len_r', len(r))
    # for t in r:
    #     print(t.title_formated, '|', t.id)
    # return
    return

    me = await sc.get_me()
    for p in await me.get_playlists():
        r = await p.delete()
        print('deleted:',r)
    # me = await sc.resolve('https://soundcloud.com/milkmen90')#await sc.get_me()
    return


    bb = [
        1978230163,
        2216330357,
        1563215512,
        2215406927,
        93331125,
        950681233,
        2005518347,
        2216251388,
        1191493201,
        1088285200,
        1276119112,
        1974815895,
        1410698692,
        306470944,
    ]
    p = await sc.create_playlist('test', track_ids=bb)
    print(p)
    print(p.to_dict())
    print(p.tracks)
    print(p.track_count)
    for t in await p.get_tracks():
        print(t.title_formated)

if __name__ == "__main__":
    asyncio.run(main())
