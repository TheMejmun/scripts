import logging
import requests
import time
from encoding import encode

# primary_release_year specifies the primary release, while year would specify any release for that title (dvd, theatrical, etc.)
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie?query={query}&primary_release_year={year}&include_adult=true&language=en-US&page={page}"
TMDB_SEARCH_URL_NO_YEAR = "https://api.themoviedb.org/3/search/movie?query={query}&include_adult=true&language=en-US&page={page}"
TMDB_BY_ID_URL = "https://api.themoviedb.org/3/movie/{id}?language=en-US"

log = logging.getLogger(__name__)


def get(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 429:
        log.warning(f"Rate limit exceeded, sleeping for 10 seconds.")
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


def get_tmdb_by_title_and_year(api_token, title, year):
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_token}"
    }

    page = 1
    max_page = 1
    results = []
    while page <= max_page:
        url = TMDB_SEARCH_URL.format(query=title, page=page, year=year)
        response = get(url, headers).json()
        max_page = response["total_pages"]
        results.extend(response["results"])
        page += 1
    return results


def get_tmdb_by_title(api_token, title):
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_token}"
    }

    page = 1
    max_page = 1
    results = []
    while page <= max_page:
        url = TMDB_SEARCH_URL_NO_YEAR.format(query=title, page=page)
        response = get(url, headers).json()
        max_page = response["total_pages"]
        results.extend(response["results"])
        page += 1
    return results


def get_tmdb(api_token, tmdbid, title, year):
    # Fixes Korean titles
    title = encode(title)

    if tmdbid is not None:
        results = get_tmdb_by_id(api_token, tmdbid)

    else:
        results = get_tmdb_by_title_and_year(api_token, title, year)
        if len(results) == 0:
            log.debug(f"No results found for {title} ({year}), searching any year.")
            results = get_tmdb_by_title(api_token, title)

        if len(results) == 0:
            tmdbid_str = input(f"\nNo results found for {title} ({year}). Enter TMDB ID: ")
            if tmdbid_str.strip() != "":
                tmdbid = int(tmdbid_str.strip())
                results = get_tmdb_by_id(api_token, tmdbid)

    log.debug(f"{len(results)=} for {title} ({year}) [{tmdbid=}]")
    for result in results:
        log.debug(f"{result['title']} / {result['original_title']} ({result['release_date']})")

    return results
