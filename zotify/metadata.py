import os
import re
from pathlib import Path
import requests
from mutagen import File
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, TRCK, TPOS
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis

from zotify.config import Config

SANITIZE = ["\\", "/", ":", "*", "?", "'", "<", ">", "\""]

def sanitize_data(value):
    """ Returns given string with problematic characters removed """
    for i in SANITIZE:
        value = value.replace(i, "")
    return value.replace("|", "-")

def get_file_path(artist, album, track_title, track_number=None, playlist_name=None, is_playlist=False, is_single_track=False):
    def format_string(format_str, **kwargs):
        if not format_str.strip():
            return ""
        return format_str.format(**{k: sanitize_data(str(v)) for k, v in kwargs.items()})

    if is_single_track:
        subfolder = Config.get_single_track_folder()
        filename = format_string(Config.get_single_track_format(), artist=artist, title=track_title)
    elif is_playlist:
        subfolder = format_string(Config.get_playlist_folder_format(), playlist_name=playlist_name)
        filename = format_string(Config.get_playlist_track_format(), artist=artist, title=track_title)
    elif album:  # It's an album
        subfolder = format_string(Config.get_album_folder_format(), artist=artist, album=album)
        if track_number is not None:
            filename = format_string(Config.get_album_track_format(), track_number=str(track_number).zfill(2), title=track_title)
        else:
            filename = track_title
    else:  # It's a single track but not from a direct single track download
        subfolder = Config.get_single_track_folder()
        filename = format_string(Config.get_single_track_format(), artist=artist, title=track_title)

    # If subfolder is empty, use root path directly
    directory = Config.get_root_path() if not subfolder else os.path.join(Config.get_root_path(), subfolder)

    return os.path.join(directory, f"{filename}.{Config.get_download_format()}")

def set_audio_tags(filename, artists, title, album_name, release_year, disc_number, track_number, album_artist=None):
    audio = File(filename, easy=True)
    
    if Config.get_only_main_artist_in_artist_tag():
        audio['artist'] = album_artist if album_artist else artists[0]
    else:
        audio['artist'] = ", ".join(artists)
    
    audio['title'] = title
    audio['album'] = album_name
    audio['date'] = release_year
    audio['discnumber'] = str(disc_number)
    audio['tracknumber'] = str(track_number)
    
    if album_artist:
        audio['albumartist'] = album_artist
    
    audio.save()

def set_music_thumbnail(directory, image_url):
    """ Downloads cover artwork """
    try:
        img_path = os.path.join(directory, "folder.jpg")
        if not os.path.exists(img_path):
            img_data = requests.get(image_url).content
            with open(img_path, "wb") as img_file:
                img_file.write(img_data)
    except Exception as e:
        print(f"Error while downloading thumbnail: {str(e)}")

def conv_artist_format(artists, title, album_artist=None):
    """ Returns main artist and title with featured artists based on configuration """
    main_artist = album_artist if album_artist else artists[0]
    
    if Config.get_add_featured_artists_to_title():
        # Check if the title already contains "feat." or "ft."
        if any(x in title.lower() for x in ["feat.", "ft.", "(feat.", "(ft."]):
            return main_artist, title
        
        featured_artists = [artist for artist in artists if artist != main_artist]
        if featured_artists:
            featured_str = ", ".join(featured_artists)
            title_with_featured_artists = f"{title} (feat. {featured_str})"
        else:
            title_with_featured_artists = title
    else:
        title_with_featured_artists = title
    
    return main_artist, title_with_featured_artists