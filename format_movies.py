#!/usr/bin/env -S PYENV_VERSION=scriptenv python
import requests
import os
import argparse
import glob

ENV_TMDB = "TMDB_API_TOKEN"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Movie Formatter',
        description='Renames movies and folders',
    )
    parser.add_argument('dir', help="The input directory")
    parser.add_argument('-o', '--out-dir', help="The output directoy")
    parser.add_argument('-t', '--api-token', help="The TMDB API token")
    parser.add_argument('-d', '--dont-capitalize', action='store_true', help="Don't force capitalization on movie titles")
    #parser.add_argument('-a', '--analyse',  action='store_true', help="")
    parser.add_argument('-v', '--verbose',  action='store_true')
    args = parser.parse_args()


    if args.verbose:
        print(f"args: {vars(args)}")

    
    api_token = args.api_token
    if api_token == None:
        if not os.environ.get(ENV_TMDB):
            print(f"ERROR: No environment variable {ENV_TMDB} found, and no --api-token argument provided.")
            #parser.print_help()
            exit(1)
        api_token = os.environ[ENV_TMDB]

    if not os.path.isdir(args.dir):
        print(f"{args.dir} is not a directory.")
        exit(1)

    for movie_dir in glob.glob(os.path.join(args.dir, "*")):
        print(movie_dir)
