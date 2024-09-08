#! /usr/bin/env python3

"""
Zotify
It's like youtube-dl, but for that other music platform.
"""

import argparse
import sys
import io

from zotify.app import client
from zotify.config import CONFIG_VALUES
from zotify.termoutput import Printer

def main():
    # Ensure proper Unicode handling for input and output
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(prog='zotify',
        description='A music and podcast downloader needing only python and ffmpeg.')
    parser.add_argument('-ns', '--no-splash',
                        action='store_true',
                        help='Suppress the splash screen when loading.')
    parser.add_argument('--config-location',
                        type=str,
                        help='Specify the zconfig.json location')
    parser.add_argument('--username',
                        type=str,
                        help='Account username')
    parser.add_argument('--password',
                        type=str,
                        help='Account password')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Enable verbose output')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('urls',
                       type=str,
                       default='',
                       nargs='*',
                       help='Downloads the track, album, playlist, podcast episode, or all albums by an artist from a url. Can take multiple urls.')
    group.add_argument('-l', '--liked',
                       dest='liked_songs',
                       action='store_true',
                       help='Downloads all the liked songs from your account.')
    group.add_argument('-f', '--followed',
                       dest='followed_artists',
                       action='store_true',
                       help='Downloads all the songs from all your followed artists.')
    group.add_argument('-p', '--playlist',
                       action='store_true',
                       help='Downloads a saved playlist from your account.')
    group.add_argument('-s', '--search',
                       type=str,
                       nargs='?',
                       const=' ',
                       help='Loads search prompt to find then download a specific track, album or playlist')
    group.add_argument('-d', '--download',
                       type=str,
                       help='Downloads tracks, playlists and albums from the URLs written in the file passed.')

    for configkey in CONFIG_VALUES:
        parser.add_argument(CONFIG_VALUES[configkey]['arg'],
                            type=str,
                            default=None,
                            help='Specify the value of the ['+configkey+'] config value')

    parser.set_defaults(func=client)

    args = parser.parse_args()
    
    # Set verbose mode
    Printer.set_verbose_mode(args.verbose)

    # If no URLs are provided, prompt the user for input
    if not args.urls and not args.liked_songs and not args.followed_artists and not args.playlist and not args.search and not args.download:
        print("Enter Spotify URL or search query:")
        user_input = input().strip()
        if user_input.startswith('https://'):
            args.urls = [user_input]
        else:
            args.search = user_input

    args.func(args)

    # Print summary after download is complete
    Printer.print_summary()


if __name__ == '__main__':
    main()
