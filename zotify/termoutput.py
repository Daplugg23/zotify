from enum import Enum
from tqdm import tqdm

from zotify.config import *
from zotify.zotify import Zotify


class PrintChannel(Enum):
    SPLASH = PRINT_SPLASH
    SKIPS = PRINT_SKIPS
    DOWNLOAD_PROGRESS = PRINT_DOWNLOAD_PROGRESS
    ERRORS = PRINT_ERRORS
    WARNINGS = PRINT_WARNINGS
    DOWNLOADS = PRINT_DOWNLOADS
    API_ERRORS = PRINT_API_ERRORS
    PROGRESS_INFO = PRINT_PROGRESS_INFO


ERROR_CHANNEL = [PrintChannel.ERRORS, PrintChannel.API_ERRORS]


class Printer:
    download_progress = None
    verbose_mode = False

    @staticmethod
    def print(channel: PrintChannel, msg: str) -> None:
        if Zotify.CONFIG.get(channel.value):
            if channel in ERROR_CHANNEL:
                print(msg, file=sys.stderr)
            else:
                print(msg)

    @staticmethod
    def print_loader(channel: PrintChannel, msg: str) -> None:
        if Zotify.CONFIG.get(channel.value):
            print(msg, flush=True, end="")

    @staticmethod
    def progress(iterable=None, desc=None, total=None, unit='it', disable=False, unit_scale=False, unit_divisor=1000):
        if not Zotify.CONFIG.get(PrintChannel.DOWNLOAD_PROGRESS.value):
            disable = True
        return tqdm(iterable=iterable, desc=desc, total=total, disable=disable, unit=unit, unit_scale=unit_scale, unit_divisor=unit_divisor)

    @staticmethod
    def set_verbose_mode(mode: bool):
        Printer.verbose_mode = mode

    @staticmethod
    def init_download_progress(total_tracks: int):
        from zotify.track import DownloadProgress
        Printer.download_progress = DownloadProgress(total_tracks)

    @staticmethod
    def update_download_progress(status: str):
        if Printer.download_progress:
            Printer.download_progress.update(status)

    @staticmethod
    def print_track_info(track_number: int, total_tracks: int, title: str, artist: str, file_size: str, quality: str):
        if Printer.verbose_mode:
            print(f"[{track_number}/{total_tracks}] Downloading: {title} by {artist} ({file_size}, {quality})")

    @staticmethod
    def print_summary():
        if Printer.download_progress:
            print("\nDownload Summary:")
            print(f"Total tracks: {Printer.download_progress.total_tracks}")
            print(f"Successfully downloaded: {Printer.download_progress.downloaded_tracks}")
            print(f"Skipped: {Printer.download_progress.skipped_tracks}")
            print(f"Failed: {Printer.download_progress.failed_tracks}")
            Printer.download_progress.stop()
