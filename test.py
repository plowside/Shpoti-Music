import asyncio
import json

from services import soundcloud

###################### SOUNDCLOUD ######################
async def main():
    z = soundcloud.SoundCloud()
    b = await z.search_tracks('Ivoxygen')
    print(b)
    for t in b:
        print(t.title_formated)
    return
    v = await z.resolve('https://soundcloud.com/fugu-fish-153361132/sets')
    # print(json.dumps(v.to_dict(), indent=4))
    if isinstance(v, soundcloud.User):
        print('v', v)
        playlists = await v.get_playlists()
        for playlist in playlists:
            print('title', playlist.title)
            print('track_count', playlist.track_count)
            for track in await playlist.get_tracks():
                # if 'Как тебя забыть' in track.title_formated:
                #     print(track.to_dict())
                print(track.title_formated)
            # print(json.dumps(playlist.to_dict(), indent=4))
            print('\n\n\n=============================================\n\n\n')
    elif isinstance(v, soundcloud.Playlist):
        print(v)
    elif isinstance(v, soundcloud.Track):
        print(v)
    else:
        print(json.dumps(v, indent=4))

if __name__ == "__main__":
    asyncio.run(main())
