from pathlib import Path, PurePath
import math
import re
import time
import uuid
from typing import Any, Tuple, List

from librespot.metadata import TrackId
import ffmpy

from zotify.const import TRACKS, ALBUM, GENRES, NAME, ITEMS, DISC_NUMBER, TRACK_NUMBER, IS_PLAYABLE, ARTISTS, IMAGES, URL, \
    RELEASE_DATE, ID, TRACKS_URL, FOLLOWED_ARTISTS_URL, SAVED_TRACKS_URL, TRACK_STATS_URL, CODEC_MAP, EXT_MAP, DURATION_MS, \
    HREF, ARTISTS, WIDTH
from zotify.termoutput import Printer, PrintChannel
from zotify.utils import create_download_directory, \
    get_directory_song_ids, add_to_directory_song_ids, get_previously_downloaded, add_to_archive, fmt_seconds
from zotify.zotify import Zotify
import traceback
from zotify.loader import Loader
from zotify.metadata import sanitize_data, get_file_path, set_audio_tags, set_music_thumbnail, conv_artist_format
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress

console = Console()

class DownloadProgress:
    def __init__(self, total_tracks):
        self.total_tracks = total_tracks
        self.downloaded_tracks = 0
        self.skipped_tracks = 0
        self.failed_tracks = 0
        self.progress = Progress()
        self.task = self.progress.add_task("[cyan]Downloading tracks...", total=total_tracks)

    def update(self, status):
        if status == 'downloaded':
            self.downloaded_tracks += 1
        elif status == 'skipped':
            self.skipped_tracks += 1
        elif status == 'failed':
            self.failed_tracks += 1
        self.progress.update(self.task, advance=1)

    def start(self):
        self.progress.start()

    def stop(self):
        self.progress.stop()

def get_saved_tracks() -> list:
    """ Returns user's saved tracks """
    songs = []
    offset = 0
    limit = 50

    while True:
        resp = Zotify.invoke_url_with_params(
            SAVED_TRACKS_URL, limit=limit, offset=offset)
        offset += limit
        songs.extend(resp[ITEMS])
        if len(resp[ITEMS]) < limit:
            break

    return songs


def get_followed_artists() -> list:
    """ Returns user's followed artists """
    artists = []
    resp = Zotify.invoke_url(FOLLOWED_ARTISTS_URL)[1]
    for artist in resp[ARTISTS][ITEMS]:
        artists.append(artist[ID])
    
    return artists


def get_song_info(song_id) -> Tuple[List[str], List[Any], str, str, Any, Any, Any, Any, Any, Any, int]:
    """ Retrieves metadata for downloaded songs """
    with Loader(PrintChannel.PROGRESS_INFO, "Fetching track information..."):
        (raw, info) = Zotify.invoke_url(f'{TRACKS_URL}?ids={song_id}&market=from_token')

    if not TRACKS in info:
        raise ValueError(f'Invalid response from TRACKS_URL:\n{raw}')

    try:
        artists = []
        for data in info[TRACKS][0][ARTISTS]:
            artists.append(data[NAME])

        album_name = info[TRACKS][0][ALBUM][NAME]
        name = info[TRACKS][0][NAME]
        release_year = info[TRACKS][0][ALBUM][RELEASE_DATE].split('-')[0]
        disc_number = info[TRACKS][0][DISC_NUMBER]
        track_number = info[TRACKS][0][TRACK_NUMBER]
        scraped_song_id = info[TRACKS][0][ID]
        is_playable = info[TRACKS][0][IS_PLAYABLE]
        duration_ms = info[TRACKS][0][DURATION_MS]

        image = info[TRACKS][0][ALBUM][IMAGES][0]
        for i in info[TRACKS][0][ALBUM][IMAGES]:
            if i[WIDTH] > image[WIDTH]:
                image = i
        image_url = image[URL]

        return artists, info[TRACKS][0][ARTISTS], album_name, name, image_url, release_year, disc_number, track_number, scraped_song_id, is_playable, duration_ms
    except Exception as e:
        raise ValueError(f'Failed to parse TRACKS_URL response: {str(e)}\n{raw}')


def get_song_genres(rawartists: List[str], track_name: str) -> List[str]:
    if Zotify.CONFIG.get_save_genres():
        try:
            genres = []
            for data in rawartists:
                # query artist genres via href, which will be the api url
                with Loader(PrintChannel.PROGRESS_INFO, "Fetching artist information..."):
                    (raw, artistInfo) = Zotify.invoke_url(f'{data[HREF]}')
                if Zotify.CONFIG.get_all_genres() and len(artistInfo[GENRES]) > 0:
                    for genre in artistInfo[GENRES]:
                        genres.append(genre)
                elif len(artistInfo[GENRES]) > 0:
                    genres.append(artistInfo[GENRES][0])

            if len(genres) == 0:
                console.print(Text(f"No genres found for song {track_name}", style="yellow"))
                genres.append('')

            return genres
        except Exception as e:
            raise ValueError(f'Failed to parse GENRES response: {str(e)}\n{raw}')
    else:
        return ['']


def get_song_lyrics(song_id: str, file_save: str) -> None:
    raw, lyrics = Zotify.invoke_url(f'https://spclient.wg.spotify.com/color-lyrics/v2/track/{song_id}')

    if lyrics:
        try:
            formatted_lyrics = lyrics['lyrics']['lines']
        except KeyError:
            raise ValueError(f'Failed to fetch lyrics: {song_id}')
        if(lyrics['lyrics']['syncType'] == "UNSYNCED"):
            with open(file_save, 'w+', encoding='utf-8') as file:
                for line in formatted_lyrics:
                    file.writelines(line['words'] + '\n')
            return
        elif(lyrics['lyrics']['syncType'] == "LINE_SYNCED"):
            with open(file_save, 'w+', encoding='utf-8') as file:
                for line in formatted_lyrics:
                    timestamp = int(line['startTimeMs'])
                    ts_minutes = str(math.floor(timestamp / 60000)).zfill(2)
                    ts_seconds = str(math.floor((timestamp % 60000) / 1000)).zfill(2)
                    ts_millis = str(math.floor(timestamp % 1000))[:2].zfill(2)
                    file.writelines(f'[{ts_minutes}:{ts_seconds}.{ts_millis}]' + line['words'] + '\n')
            return
    raise ValueError(f'Failed to fetch lyrics: {song_id}')


def get_song_duration(song_id: str) -> float:
    """ Retrieves duration of song in second as is on spotify """

    (raw, resp) = Zotify.invoke_url(f'{TRACK_STATS_URL}{song_id}')

    # get duration in miliseconds
    ms_duration = resp['duration_ms']
    # convert to seconds
    duration = float(ms_duration)/1000

    return duration


def download_track(mode: str, track_id: str, extra_keys=None, disable_progressbar=False) -> None:
    """ Downloads raw song audio from Spotify """

    if extra_keys is None:
        extra_keys = {}

    prepare_download_loader = Loader(PrintChannel.PROGRESS_INFO, "Preparing download...")
    prepare_download_loader.start()

    try:
        (artists, raw_artists, album_name, name, image_url, release_year, disc_number,
         track_number, scraped_song_id, is_playable, duration_ms) = get_song_info(track_id)

        song_name = sanitize_data(artists[0]) + ' - ' + sanitize_data(name)

        filename = get_file_path(artists[0], album_name, name, track_number, extra_keys.get('playlist_name'), mode == 'playlist', mode == 'single')
        filedir = PurePath(filename).parent

        filename_temp = filename
        if Zotify.CONFIG.get_temp_download_dir() != '':
            filename_temp = PurePath(Zotify.CONFIG.get_temp_download_dir()).joinpath(f'zotify_{str(uuid.uuid4())}_{track_id}.{Path(filename).suffix}')

        check_name = Path(filename).is_file() and Path(filename).stat().st_size
        check_id = scraped_song_id in get_directory_song_ids(filedir)
        check_all_time = scraped_song_id in get_previously_downloaded()

        # a song with the same name is installed
        if not check_id and check_name:
            c = len([file for file in Path(filedir).iterdir() if re.search(f'^{filename}_', str(file))]) + 1

            fname = PurePath(PurePath(filename).name).parent
            ext = PurePath(PurePath(filename).name).suffix

            filename = PurePath(filedir).joinpath(f'{fname}_{c}{ext}')

        # Initialize download_progress if it doesn't exist
        if Printer.download_progress is None:
            total_tracks = int(extra_keys.get('total_tracks', 1))
            Printer.init_download_progress(total_tracks)

    except Exception as e:
        console.print(Panel(f"[red]Error: Skipping song - Failed to query metadata[/red]"))
        console.print(f"[red]Track ID: {track_id}[/red]")
        for k in extra_keys:
            console.print(f"[red]{k}: {extra_keys[k]}[/red]")
        console.print("\n")
        console.print(f"[red]{str(e)}[/red]\n")
        console.print(Text("".join(traceback.TracebackException.from_exception(e).format()), style="red"))
        Printer.update_download_progress('failed')

    else:
        try:
            if not is_playable:
                prepare_download_loader.stop()
                console.print(Panel(f"[yellow]Skipping: {song_name} (Song is unavailable)[/yellow]"))
                Printer.update_download_progress('skipped')
            else:
                if check_id and check_name and Zotify.CONFIG.get_skip_existing():
                    prepare_download_loader.stop()
                    console.print(Panel(f"[yellow]Skipping: {song_name} (Song already exists)[/yellow]"))
                    Printer.update_download_progress('skipped')

                elif check_all_time and Zotify.CONFIG.get_skip_previously_downloaded():
                    prepare_download_loader.stop()
                    console.print(Panel(f"[yellow]Skipping: {song_name} (Song already downloaded once)[/yellow]"))
                    Printer.update_download_progress('skipped')

                else:
                    if track_id != scraped_song_id:
                        track_id = scraped_song_id
                    track = TrackId.from_base62(track_id)
                    stream = Zotify.get_content_stream(track, Zotify.DOWNLOAD_QUALITY)
                    create_download_directory(filedir)
                    total_size = stream.input_stream.size

                    prepare_download_loader.stop()

                    time_start = time.time()
                    downloaded = 0
                    with open(filename_temp, 'wb') as file, Printer.progress(
                            desc=song_name,
                            total=total_size,
                            unit='B',
                            unit_scale=True,
                            unit_divisor=1024,
                            disable=disable_progressbar
                    ) as p_bar:
                        b = 0
                        while b < 5:
                            data = stream.input_stream.stream().read(Zotify.CONFIG.get_chunk_size())
                            p_bar.update(file.write(data))
                            downloaded += len(data)
                            b += 1 if data == b'' else 0
                            if Zotify.CONFIG.get_download_real_time():
                                delta_real = time.time() - time_start
                                delta_want = (downloaded / total_size) * (duration_ms/1000)
                                if delta_want > delta_real:
                                    time.sleep(delta_want - delta_real)

                    time_downloaded = time.time()

                    genres = get_song_genres(raw_artists, name)

                    if(Zotify.CONFIG.get_download_lyrics()):
                        try:
                            get_song_lyrics(track_id, PurePath(str(filename)[:-3] + "lrc"))
                            console.print(Text(f"Lyrics downloaded for {name}", style="green"))
                        except ValueError:
                            console.print(Text(f"Lyrics not available for {name}", style="yellow"))
                    convert_audio_format(filename_temp)
                    try:
                        main_artist, title_with_featured = conv_artist_format(artists, name)
                        set_audio_tags(filename_temp, artists, title_with_featured, album_name, release_year, disc_number, track_number, main_artist)
                        set_music_thumbnail(PurePath(filename_temp).parent, image_url)
                    except Exception:
                        console.print(Text("Unable to write metadata, ensure ffmpeg is installed and added to your PATH.", style="red"))

                    if filename_temp != filename:
                        Path(filename_temp).rename(filename)

                    time_finished = time.time()

                    console.print(Panel(f"[green]Downloaded:[/green] {song_name}\n[blue]To:[/blue] {Path(filename).relative_to(Zotify.CONFIG.get_root_path())}\n[cyan]Time:[/cyan] {fmt_seconds(time_downloaded - time_start)} (plus {fmt_seconds(time_finished - time_downloaded)} converting)"))
                    Printer.print_track_info(track_number, Printer.download_progress.total_tracks, name, artists[0], f"{total_size / 1024 / 1024:.2f}MB", Zotify.DOWNLOAD_QUALITY)

                    # add song id to archive file
                    if Zotify.CONFIG.get_skip_previously_downloaded():
                        add_to_archive(scraped_song_id, PurePath(filename).name, artists[0], name)
                    # add song id to download directory's .song_ids file
                    if not check_id:
                        add_to_directory_song_ids(filedir, scraped_song_id, PurePath(filename).name, artists[0], name)

                    Printer.update_download_progress('downloaded')

                    if Zotify.CONFIG.get_bulk_wait_time():
                        time.sleep(Zotify.CONFIG.get_bulk_wait_time())
        except Exception as e:
            console.print(Panel(f"[red]Error: Skipping {song_name} (General download error)[/red]"))
            console.print(f"[red]Track ID: {track_id}[/red]")
            for k in extra_keys:
                console.print(f"[red]{k}: {extra_keys[k]}[/red]")
            console.print("\n")
            console.print(f"[red]{str(e)}[/red]\n")
            console.print(Text("".join(traceback.TracebackException.from_exception(e).format()), style="red"))
            if Path(filename_temp).exists():
                Path(filename_temp).unlink()
            Printer.update_download_progress('failed')

    prepare_download_loader.stop()


def convert_audio_format(filename) -> None:
    """ Converts raw audio into playable file """
    temp_filename = f'{PurePath(filename).parent}.tmp'
    Path(filename).replace(temp_filename)

    download_format = Zotify.CONFIG.get_download_format().lower()
    file_codec = CODEC_MAP.get(download_format, 'copy')
    if file_codec != 'copy':
        bitrate = Zotify.CONFIG.get_transcode_bitrate()
        bitrates = {
            'auto': '320k' if Zotify.check_premium() else '160k',
            'normal': '96k',
            'high': '160k',
            'very_high': '320k'
        }
        bitrate = bitrates[Zotify.CONFIG.get_download_quality()]
    else:
        bitrate = None

    output_params = ['-c:a', file_codec]
    if bitrate:
        output_params += ['-b:a', bitrate]

    try:
        ff_m = ffmpy.FFmpeg(
            global_options=['-y', '-hide_banner', '-loglevel error'],
            inputs={temp_filename: None},
            outputs={filename: output_params}
        )
        with Loader(PrintChannel.PROGRESS_INFO, "Converting file..."):
            ff_m.run()

        if Path(temp_filename).exists():
            Path(temp_filename).unlink()

    except ffmpy.FFExecutableNotFoundError:
        console.print(Text(f"[yellow]SKIPPING {file_codec.upper()} CONVERSION - FFMPEG NOT FOUND[/yellow]"))
