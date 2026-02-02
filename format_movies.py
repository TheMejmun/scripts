#!/usr/bin/env -S PYENV_VERSION=scriptenv python
import requests
import os
import argparse

#ENV_TMDB = "TMDB_API_TOKEN"
#if not os.environ.get(ENV_TMDB):
#    print(f"No environment variable {ENV_TMDB} found.")
#    exit(1)
#tmdb_token = os.environ[ENV_TMDB]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Movie Formatter',
        description='Renames movies and folders',
        epilog='Text at the bottom of help'
    )
    parser.add_argument('dir', help="The input directory")
    parser.add_argument('-o', '--out-dir', help="The output directoy")
    parser.add_argument('-t', '--api-token', help="The TMDB API token")
    parser.add_argument('-d', '--dont-capitalize', action='store_false', help="Don't force capitalization on movie titles")
    parser.add_argument('-v', '--verbose',  action='store_true')
    args = parser.parse_args()

    if args.verbose:
        print(f"args: {vars(args)}")
    
