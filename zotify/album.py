from zotify.const import ALBUM_URL, ALBUM, NAME, TRACKS, ITEMS, TOTAL, ID, RELEASE_DATE
from zotify.track import download_track
from zotify.utils import fix_filename
from zotify.termoutput import Printer, PrintChannel
from zotify.zotify import Zotify
from pathlib import Path

def get_album_tracks(album_id):
    """ returns list of album's tracks """
    url = f'{ALBUM_URL}{album_id}'
    (raw, album_json) = Zotify.invoke_url(url)

    tracks = []
    total_tracks = album_json[TRACKS][TOTAL]
    iteration = 0
    while len(tracks) < total_tracks:
        if iteration == 0:
            tracks = album_json[TRACKS][ITEMS]
        else:
            (raw, album_json) = Zotify.invoke_url(f'{url}/tracks?offset={len(tracks)}&limit=50')
            tracks += album_json[ITEMS]
        iteration += 1
    
    return tracks

def download_album(album_id):
    """ Downloads entire album """

    (raw, album) = Zotify.invoke_url(ALBUM_URL + album_id)

    if ALBUM not in album:
        artist = fix_filename(album[NAME])
        album_name = fix_filename(album[NAME])
    else:
        artist = fix_filename(album[ALBUM][NAME])
        album_name = fix_filename(album[ALBUM][NAME])

    release_year = album[RELEASE_DATE].split('-')[0]
    total_tracks = album[TRACKS][TOTAL]
    download_dir = Path(Zotify.CONFIG.get_root_path(), f"{artist} - {album_name}")

    Printer.print(PrintChannel.SKIPS, f"\nDownloading Album: {album_name}")

    tracks = get_album_tracks(album_id)
    n = 1
    for track in tracks:
        download_track('album', track[ID], extra_keys={
            'album_num': str(n).zfill(2),
            'artist': artist,
            'album': album_name,
            'album_id': album_id,
            'release_year': release_year,
            'total_tracks': total_tracks
        }, disable_progressbar=True)
        n += 1

def download_artist_albums(artist_id):
    """ Downloads all of an artist's albums """

    (raw, albums) = Zotify.invoke_url(f'https://api.spotify.com/v1/artists/{artist_id}/albums')

    Printer.print(PrintChannel.SKIPS, "\nDownloading Discography")

    for album in albums[ITEMS]:
        download_album(album[ID])
