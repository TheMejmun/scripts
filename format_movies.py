#!/usr/bin/env -S PYENV_VERSION=scriptenv python
from tabnanny import verbose

import requests
import os
import argparse
import shutil
import re
import unicodedata
import time

ENV_TMDB = "TMDB_API_TOKEN"

TITLE_REGEX_PART = r"(?P<title>.+)"
YEAR_REGEX_PART = r"\((?P<year>[0-9][0-9][0-9][0-9])\)"
PROVIDER_REGEX_PART = r"(\s\[tmdbid-(?P<tmdbid>[0-9]+)\])?"  # Could have multiple
LABEL_REGEX_PART = r"(\s-\s\[?(?P<label>[\w\s]+)\]?)?"
DIR_REGEX = rf"^{TITLE_REGEX_PART}\s{YEAR_REGEX_PART}{PROVIDER_REGEX_PART}.*$"
FILE_REGEX = rf"^.*{LABEL_REGEX_PART}\.(?P<extension>[\w]+)$"

# primary_release_year specifies the primary release, while year would specify any release for that title (dvd, theatrical, etc.)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie?query={query}&primary_release_year={year}&include_adult=true&language=en-US&page={page}"
TMDB_SEARCH_URL_NO_YEAR = "https://api.themoviedb.org/3/search/movie?query={query}&include_adult=true&language=en-US&page={page}"
TMDB_BY_ID_URL = "https://api.themoviedb.org/3/movie/{id}?language=en-US"

# https://jellyfin.org/docs/general/clients/codec-support/
MOVIE_EXTENSIONS = ["mkv", "mp4", "avi", "mov", "webm", "ts", "ogg"]


def normalize(title, verbose=False):
    # Replace all non-word characters
    fixed_encoding = unicodedata.normalize('NFC', title)
    norm = re.sub(r"\W+", " ", fixed_encoding.lower()).strip()
    if verbose: print(f"{title} -> {norm=}")
    return norm


def parse_folder(path, verbose):
    data = {"path": path}

    if match := re.match(DIR_REGEX, os.path.basename(path)):
        data.update(match.groupdict())
    else:
        print(f"ERROR: Could not parse {path}. Skipping.")
        return None

    data["files"] = {}
    for dir_content in os.scandir(path):
        file_name = dir_content.name
        data["files"][file_name] = {"path": dir_content.path}
        if match := re.match(FILE_REGEX, file_name):
            data["files"][file_name].update(match.groupdict())
        else:
            data["files"][file_name].update({"label": None, "extension": None})

    if len(data["files"]) == 0: print(f"WARNING: {path} is empty.")
    if verbose: print(f"{data=}")
    return data


def get(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 429:
        print(f"WARNING: Rate limit exceeded, sleeping for 10 seconds.")
        time.sleep(10)
        return get(url, headers)
    elif response.status_code != 200:
        raise Exception(f"Error {response.status_code} while getting {url}")
    return response


def get_tmdb_by_id(api_token, tmdbid):
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    url = TMDB_BY_ID_URL.format(id=tmdbid)
    response = get(url, headers).json()
    return [response]


# TODO for existing tmdbid
def get_tmdb(api_token, tmdbid, title, year, verbose):
    # Fixes Korean titles
    title = unicodedata.normalize('NFC', title)

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_token}"
    }

    if tmdbid is not None:
        results = get_tmdb_by_id(api_token, tmdbid)

    else:
        page = 1
        max_page = 1
        results = []

        while page <= max_page:
            url = TMDB_SEARCH_URL.format(query=title, page=page, year=year)
            response = get(url, headers).json()
            max_page = response["total_pages"]
            results.extend(response["results"])
            page += 1

        if len(results) == 0:
            if verbose: print(f"WARNING: No results found for {title} ({year}), searching any year.")
            page = 1
            while page <= max_page:
                url = TMDB_SEARCH_URL_NO_YEAR.format(query=title, page=page, year=year)
                response = get(url, headers).json()
                max_page = response["total_pages"]
                results.extend(response["results"])
                page += 1

        if len(results) == 0:
            tmdbid_str = input(f"\nNo results found for {title} ({year}). Enter TMDB ID: ")
            if tmdbid_str.strip() != "":
                tmdbid = int(tmdbid_str.strip())
                results = get_tmdb_by_id(api_token, tmdbid)

    if verbose:
        print(f"{len(results)=} for {title} ({year}) [{tmdbid=}]")
        for result in results:
            print(f"{result['title']} / {result['original_title']} ({result['release_date']})")

    return results


def find_match(folder_data, tmdb_data, verbose):
    if len(tmdb_data) == 0: return None

    title_norm = normalize(folder_data["title"], verbose)
    tmdb_data_filtered = [
        entry
        for entry in tmdb_data
        if normalize(entry["original_title"], verbose) == title_norm or
           normalize(entry["title"], verbose) == title_norm
    ]

    if len(tmdb_data_filtered) == 1:
        return tmdb_data_filtered[0]

    else:
        print("\nPossible matches:")
        for i, entry in enumerate(tmdb_data):
            print(f"\t{i}: {entry['title']} / {entry['original_title']} ({entry['release_date']}) [{entry['id']}]")
        print(f"\t{len(tmdb_data)}: None of the above")
        print(f"For path {folder_data['path']}")
        selection = int(input(f"Select match for {folder_data['title']} ({folder_data['year']}): "))
        return None if selection == len(tmdb_data) else tmdb_data[selection]


def format_title(title, capitalize):
    elements = re.sub(r"\W+", " ", title).strip().split(" ")
    if capitalize:
        elements = [e.capitalize() for e in elements]
    title = " ".join(elements)
    return title


def format_movie(args, folder_data, tmdb_data, verbose):
    if tmdb_data is None:
        title = format_title(folder_data["title"], not args.dont_capitalize)
        year = folder_data["year"]
        tmdbid = None
    else:
        title = format_title(tmdb_data["original_title"], not args.dont_capitalize)
        year = tmdb_data["release_date"].split("-")[0]
        tmdbid = tmdb_data["id"]

    if verbose: print(f"Formatting {folder_data['path']} as {title} ({year}) [{tmdbid=}]")

    out_dir = args.out_dir if args.out_dir is not None else os.path.dirname(folder_data["path"])
    folder_name = f"{title} ({year})" if tmdbid is None else f"{title} ({year}) [tmdbid-{tmdbid}]"
    dir_path = os.path.join(out_dir, folder_name)
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

    for file_name, file_data in folder_data.get("files", {}).items():
        if file_data["extension"] in MOVIE_EXTENSIONS:
            file_name = f"{folder_name} - {file_data['label']}.{file_data['extension']}" if file_data[
                "label"] else f"{folder_name}.{file_data['extension']}"

        file_path = os.path.join(dir_path, file_name)
        # Check if the new filename is different from the old one, encoding invariant
        if unicodedata.normalize('NFC', file_data["path"]) != unicodedata.normalize('NFC', file_path):
            if os.path.exists(file_path):
                raise Exception(f"File {file_path} already exists. Will not overwrite with {file_data['path']}")
            if args.move:
                shutil.move(file_data["path"], file_path)
                if verbose: print(f"Moved {file_data['path']} to {file_path}")
            else:
                shutil.copy2(file_data["path"], file_path)
                if verbose: print(f"Copied {file_data['path']} to {file_path}")
        # Check if the new filename is different from the old one in encoding alone
        elif file_data["path"] != file_path:
            if verbose: print(f"WARNING: File {file_path} is stored under a different encoding.")
            # shutil.move(file_data["path"], file_path)

        if file_data["extension"] not in MOVIE_EXTENSIONS and args.delete_unrecognised:
            print(f"Deleting unrecognised file {file_path}")
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)

    if args.move and unicodedata.normalize('NFC', folder_data["path"]) != unicodedata.normalize('NFC', dir_path):
        print(f"Deleting source folder {folder_data['path']}")
        shutil.rmtree(folder_data["path"])
    elif folder_data["path"] != dir_path:
        if verbose: print(f"WARNING: Dir {dir_path} is stored under a different encoding.")
        # shutil.move(folder_data["path"], dir_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Movie Formatter',
        description='Renames movies and folders',
    )
    parser.add_argument('dir', help="The input directory")
    parser.add_argument('-o', '--out-dir', help="The output directoy")
    parser.add_argument('-t', '--api-token', help="The TMDB API token")
    parser.add_argument('-d', '--dont-capitalize', action='store_true',
                        help="Don't force capitalization on movie titles")
    parser.add_argument('-u', '--delete-unrecognised', action='store_true', help="Delete unrecognised files")
    parser.add_argument('-m', '--move', action='store_true', help="Move files instead of copying")
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    if args.verbose: print(f"args: {vars(args)}")

    api_token = args.api_token
    if api_token is None:
        if not os.environ.get(ENV_TMDB):
            print(f"ERROR: No environment variable {ENV_TMDB} found, and no --api-token argument provided.")
            # parser.print_help()
            exit(1)
        api_token = os.environ[ENV_TMDB]

    if not os.path.isdir(args.dir):
        print(f"{args.dir} is not a directory.")
        exit(1)

    for movie_dir in os.scandir(args.dir):
        if not movie_dir.is_dir():
            continue

        folder_data = parse_folder(movie_dir.path, args.verbose)
        if folder_data is None: continue
        tmdb_data = get_tmdb(args.api_token, folder_data["tmdbid"], folder_data["title"], folder_data["year"],
                             args.verbose)

        match = find_match(folder_data, tmdb_data, args.verbose)

        format_movie(args, folder_data, match, args.verbose)
