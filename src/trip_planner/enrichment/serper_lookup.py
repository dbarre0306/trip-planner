import os
from dataclasses import dataclass, field

import requests

from trip_planner.enrichment.venue_url_selection import rank_urls

SERPER_SEARCH_URL = "https://google.serper.dev/search"
_REQUEST_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class VenueLookupResult:
    url: str | None = None
    notes: list[str] = field(default_factory=list)


def _get_serper_search_results(query: str) -> list[dict]:
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        raise RuntimeError("SERPER_API_KEY environment variable is not set")
    response = requests.post(
        SERPER_SEARCH_URL,
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
        json={"q": query},
        timeout=_REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json().get("organic", [])


def _is_reachable(url: str) -> bool:
    try:
        response = requests.head(url, timeout=_REQUEST_TIMEOUT_SECONDS, allow_redirects=True)
    except requests.RequestException:
        return False
    return response.status_code < 400


def lookup_venue(name: str, destination: str) -> VenueLookupResult:
    results = _get_serper_search_results(f"{name} '{destination}'")

    original_links = [result["link"] for result in results if result.get("link")]

    url = None
    if original_links:
        try:
            ranked_links = rank_urls(name, destination, results)
        except Exception:
            ranked_links = []

        search_order = ranked_links + [link for link in original_links if link not in ranked_links]

        for link in search_order:
            if _is_reachable(link):
                url = link
                break

    notes = [result["snippet"] for result in results if result.get("snippet")]

    return VenueLookupResult(url=url, notes=notes)
