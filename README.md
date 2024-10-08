# Zotify

### A highly customizable music and podcast downloader.

<p align="center">
  <img src="https://i.imgur.com/hGXQWSl.png" width="50%" alt="Zotify logo">
</p>

### Features
  - Downloads at up to 320kbps*
  - Downloads directly from the source**
  - Downloads podcasts, playlists, liked songs, albums, artists, singles.
  - Downloads synced lyrics from the source using a specific user agent to mimic legitimate browser requests
  - Option to download in real time to appear more legitimate***
  - Supports multiple audio formats
  - Download directly from URL or use built-in search
  - Bulk downloads from a list of URLs in a text file or parsed directly as arguments
  - Improved Unicode handling for URLs and search queries
  - Enhanced metadata handling and customization options
  - Flexible file and folder naming conventions
  - Sync lyrics for existing songs without re-downloading audio files (enabled by default)

*Free accounts are limited to 160kbps. \
**Audio files are NOT substituted with ones from other sources such as YouTube or Deezer, they are sourced directly. \
***'real time' refers to downloading at the speed it would normally be streamed at (the duration of the track).

### Install

```
Dependencies:

- Python 3.9 or greater
- FFmpeg

Installation:

python -m pip install git+https://zotify.xyz/zotify/zotify.git
```

See [INSTALLATION](INSTALLATION.md) for a more detailed and opinionated installation walkthrough.

### Command line usage

```
Basic command line usage:
  zotify <track/album/playlist/episode/artist url>   Downloads the track, album, playlist or podcast episode specified as a command line argument. If an artist url is given, all albums by specified artist will be downloaded. Can take multiple urls.

Basic options:
  (nothing)        Download the tracks/albums/playlists URLs from the parameter
  -d, --download   Download all tracks/albums/playlists URLs from the specified file
  -p, --playlist   Downloads a saved playlist from your account
  -l, --liked      Downloads all the liked songs from your account
  -f, --followed   Downloads all songs by all artists you follow
  -s, --search     Searches for specified track, album, artist or playlist, loads search prompt if none are given.  
  -h, --help       See this message.
```

### Options

All these options can either be configured in the config or via the commandline, in case of both the commandline-option has higher priority.  
Be aware you have to set boolean values in the commandline like this: `--download-real-time=True`

| Key (config)                 | Commandline parameter            | Defaults | Description
|------------------------------|----------------------------------|----------|---------------------------------------------------------------------|
| CREDENTIALS_LOCATION         | --credentials-location           |          | The location of the credentials.json
| OUTPUT                       | --output                         |          | The output location/format (see below)
| SONG_ARCHIVE                 | --song-archive                   |          | The song_archive file for SKIP_PREVIOUSLY_DOWNLOADED
| ROOT_PATH                    | --root-path                      |          | Directory where Zotify saves music
| ROOT_PODCAST_PATH            | --root-podcast-path              |          | Directory where Zotify saves podcasts
| SPLIT_ALBUM_DISCS            | --split-album-discs              | False    | Saves each disk in its own folder
| DOWNLOAD_LYRICS              | --download-lyrics                | True     | Downloads synced lyrics in .lrc format, uses unsynced as fallback.
| SYNC_LYRICS_ONLY_MODE        | --sync-lyrics-only-mode          | True     | Only download lyrics for existing songs, don't download audio files
| MD_ALLGENRES                 | --md-allgenres                   | False    | Save all relevant genres in metadata
| MD_GENREDELIMITER            | --md-genredelimiter              | ,        | Delimiter character used to split genres in metadata
| DOWNLOAD_FORMAT              | --download-format                | ogg      | The download audio format (aac, fdk_aac, m4a, mp3, ogg, opus, vorbis)
| DOWNLOAD_QUALITY             | --download-quality               | auto     | Audio quality of downloaded songs (normal, high, very_high*)
| TRANSCODE_BITRATE            | --transcode-bitrate              | auto     | Overwrite the bitrate for ffmpeg encoding
| SKIP_EXISTING_FILES          | --skip-existing                  | True     | Skip songs with the same name
| SKIP_PREVIOUSLY_DOWNLOADED   | --skip-previously-downloaded     | False    | Use a song_archive file to skip previously downloaded songs
| RETRY_ATTEMPTS               | --retry-attempts                 | 1        | Number of times Zotify will retry a failed request
| BULK_WAIT_TIME               | --bulk-wait-time                 | 1        | The wait time between bulk downloads
| OVERRIDE_AUTO_WAIT           | --override-auto-wait             | False    | Totally disable wait time between songs with the risk of instability
| CHUNK_SIZE                   | --chunk-size                     | 20000    | Chunk size for downloading
| DOWNLOAD_REAL_TIME           | --download-real-time             | False    | Downloads songs as fast as they would be played, should prevent account bans.
| LANGUAGE                     | --language                       | en       | Language for spotify metadata
| PRINT_SPLASH                 | --print-splash                   | False    | Show the Zotify logo at startup
| PRINT_SKIPS                  | --print-skips                    | True     | Show messages if a song is being skipped
| PRINT_DOWNLOAD_PROGRESS      | --print-download-progress        | True     | Show download/playlist progress bars
| PRINT_ERRORS                 | --print-errors                   | True     | Show errors
| PRINT_DOWNLOADS              | --print-downloads                | False    | Print messages when a song is finished downloading
| TEMP_DOWNLOAD_DIR            | --temp-download-dir              |          | Download tracks to a temporary directory first
| SINGLE_TRACK_FOLDER          | --single-track-folder            | Singles  | Folder name for single tracks
| SINGLE_TRACK_FORMAT          | --single-track-format            | {artist} - {title} | Format for single track filenames
| ALBUM_FOLDER_FORMAT          | --album-folder-format            | {artist} - {album} | Format for album folder names
| ALBUM_TRACK_FORMAT           | --album-track-format             | {track_number} - {title} | Format for album track filenames
| PLAYLIST_FOLDER_FORMAT       | --playlist-folder-format         | {playlist_name} | Format for playlist folder names
| PLAYLIST_TRACK_FORMAT        | --playlist-track-format          | {artist} - {title} | Format for playlist track filenames
| ADD_FEATURED_ARTISTS_TO_TITLE| --add-featured-artists-to-title  | True     | Add featured artists to track titles
| ONLY_MAIN_ARTIST_IN_ARTIST_TAG| --only-main-artist-in-artist-tag| True     | Include only the main artist in the artist tag

*very-high is limited to premium only  

### Sync Lyrics Only Mode

The `SYNC_LYRICS_ONLY_MODE` (or `--sync-lyrics-only-mode` in command line) is a feature that allows you to download only the lyrics for songs that already exist in your library, without re-downloading the audio files. This is particularly useful when you want to add lyrics to your existing music collection.

This mode is enabled by default (set to `True`). When this mode is active:
1. For existing songs in your library, Zotify will attempt to download only the lyrics.
2. For new songs that don't exist in your library, Zotify will download both the audio file and the lyrics as usual.

This feature works in conjunction with the `DOWNLOAD_LYRICS` option. Make sure `DOWNLOAD_LYRICS` is set to `True` for the `SYNC_LYRICS_ONLY_MODE` to have any effect.

To disable this feature, you can either:
1. Set `SYNC_LYRICS_ONLY_MODE` to `False` in your config file, or
2. Use the `--sync-lyrics-only-mode=False` command line argument when running Zotify.

Example usage to disable the feature:
```
zotify --sync-lyrics-only-mode=False <album/playlist URL>
```

This will download both audio and lyrics for all songs in the album or playlist, regardless of whether they already exist in your library.

### Configuration 

You can find the configuration file in following locations:  
| OS              | Location          
|-----------------|-------------------------------------------------------------------|
| Windows         | `C:\Users\<USERNAME>\AppData\Roaming\Zotify\config.json`          |
| MacOS           | `/Users/<USERNAME>/Library/ApplicationSupport/Zotify/config.json` |
| Linux           | `/home/<USERNAME>/.config/zotify/config.json`                     |

To log out, just remove the configuration file. Uninstalling Zotify does not remove the config file.

### Output format

With the option `OUTPUT` (or the commandline parameter `--output`) you can specify the output location and format.  
The value is relative to the `ROOT_PATH`/`ROOT_PODCAST_PATH` directory and can contain the following placeholder:

| Placeholder     | Description
|-----------------|--------------------------------
| {artist}        | The song artist
| {album}         | The song album
| {song_name}     | The song name
| {release_year}  | The song release year
| {disc_number}   | The disc number
| {track_number}  | The track_number
| {id}            | The song id
| {track_id}      | The track id
| {ext}           | The file extension
| {album_id}      | (only when downloading albums) ID of the album
| {album_num}     | (only when downloading albums) Incrementing track number
| {playlist}      | (only when downloading playlists) Name of the playlist 
| {playlist_num}  | (only when downloading playlists) Incrementing track number

Example values could be:
~~~~
{playlist}/{artist} - {song_name}.{ext}
{playlist}/{playlist_num} - {artist} - {song_name}.{ext}
{artist} - {song_name}.{ext}
{artist}/{album}/{album_num} - {artist} - {song_name}.{ext}
~~~~

### Docker Usage
```
Build the docker image from the Dockerfile:
  docker build -t zotify .
Create and run a container from the image:
  docker run --rm -v "$PWD/Zotify Music:/root/Music/Zotify Music" -v "$PWD/Zotify Podcasts:/root/Music/Zotify Podcasts" -it zotify
```

### Recent Updates

1. Enhanced metadata handling:
   - Added options for customizing file and folder naming conventions.
   - Improved handling of featured artists in track titles and tags.
2. Improved file organization:
   - Added separate configuration options for single tracks, album tracks, and playlist tracks.
3. Enhanced error handling and output clarity:
   - Suppressed redundant Spotify API Error messages.
   - Simplified the lyrics download process to only show "Lyrics not available" messages when appropriate.
4. Consistent behavior when running Zotify through the batch file or directly from the terminal.
5. Added prompt for input when no URL is provided as an argument.
6. Improved Unicode handling for URLs and search queries.
7. Added a specific user agent for authentication to enable synced lyrics download.
8. Introduced `SYNC_LYRICS_ONLY_MODE` to download lyrics for existing songs without re-downloading audio files (enabled by default).

### What do I do if I see "Your session has been terminated"?

If you see this, don't worry! Just try logging back in. If you see the incorrect username or password error, reset your password and you should be able to log back in.

### Will my account get banned if I use this tool?

Currently no user has reported their account getting banned after using Zotify.

It is recommended you use Zotify with a burner account.
Alternatively, there is a configuration option labeled ```DOWNLOAD_REAL_TIME```, this limits the download speed to the duration of the song being downloaded thus appearing less suspicious.
This option is much slower and is only recommended for premium users who wish to download songs in 320kbps without buying premium on a burner account.

### Disclaimer
Zotify is intended to be used in compliance with DMCA, Section 1201, for educational, private and fair use. \
Zotify contributors are not responsible for any misuse of the program or source code.

### Contributing

Please refer to [CONTRIBUTING](CONTRIBUTING.md)

### Changelog

Please refer to [CHANGELOG](CHANGELOG.md)
