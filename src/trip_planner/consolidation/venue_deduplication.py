import difflib
import json
import random
import re
from typing import Iterable
from urllib.parse import urlparse

from trip_planner.core.models import GeoLocation, Venue
from trip_planner.integrations.openai_client import chat_completion

_NAME_SIMILARITY_THRESHOLD = 0.85
_GEO_MATCH_DEGREES = 0.0015  # roughly ~150m at mid-latitudes

_ADDRESS_WORD_EXPANSIONS = {
    "st": "street",
    "ave": "avenue",
    "rd": "road",
    "dr": "drive",
    "blvd": "boulevard",
    "ln": "lane",
    "pl": "place",
    "ct": "court",
}

_ADDRESS_UNIT_RE = re.compile(r"\b(ste|suite|unit|apt|#)\s*\.?\s*\d+\w*\b")

_GROUPING_INSTRUCTIONS = (
    "Some of these venues may describe the same real-world place — the same or a "
    "near-identical name (ignoring case, whitespace, and minor spelling variation), a "
    "matching website URL, and/or a matching street address or coordinates (tolerating "
    "formatting differences), regardless of whether they're tagged with different interests.\n\n"
    "Group together the ids of venues that describe the same real-world place. Within each "
    "group, order the ids from most specific to least specific — for example, a restaurant "
    "inside a hotel is more specific than the hotel itself, so the restaurant's id should come "
    "first.\n\n"
    "Only include groups with two or more ids. Do not include a venue in any group if it "
    "doesn't share a real-world place with another venue in the list.\n\n"
    "Respond with ONLY a JSON object with exactly one key, \"groups\", whose value is a list of "
    "groups, each group being a list of ids ordered from most specific to least specific."
)


def _build_prompt(venues: list[tuple[int, Venue]]) -> str:
    lines = ["Venues:"]
    for identifier, venue in venues:
        lines.append(f"- id: {identifier}")
        lines.append(f"  name: {venue.name}")
        if venue.url:
            lines.append(f"  url: {venue.url}")
        if venue.location:
            lines.append(f"  location: {venue.location}")
        if venue.geo_location:
            lines.append(
                f"  coordinates: {venue.geo_location.latitude}, {venue.geo_location.longitude}"
            )
    lines.append("")
    lines.append(_GROUPING_INSTRUCTIONS)
    return "\n".join(lines)


def _parse_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if "\n" in cleaned:
            cleaned = cleaned.split("\n", 1)[1]
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _extract_ids(raw_group: object, valid_ids: set[int]) -> tuple[list[int], bool]:
    """Returns the valid ids found in raw_group and whether their order is usable."""

    def _collect(values: Iterable[object]) -> list[int]:
        ids: list[int] = []
        seen: set[int] = set()
        for entry in values:
            if not isinstance(entry, int) or isinstance(entry, bool):
                continue
            if entry not in valid_ids or entry in seen:
                continue
            seen.add(entry)
            ids.append(entry)
        return ids

    if isinstance(raw_group, list):
        return _collect(raw_group), True
    if isinstance(raw_group, dict):
        return _collect(raw_group.values()), False
    return [], False


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip().casefold()


def _names_match(a: str, b: str) -> bool:
    normalized_a, normalized_b = _normalize_name(a), _normalize_name(b)
    if normalized_a == normalized_b:
        return True
    ratio = difflib.SequenceMatcher(None, normalized_a, normalized_b).ratio()
    return ratio >= _NAME_SIMILARITY_THRESHOLD


def _normalize_url(url: str) -> str:
    parsed = urlparse(url if "//" in url else f"//{url}")
    netloc = parsed.netloc.casefold()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return f"{netloc}{parsed.path.rstrip('/')}"


def _urls_match(a: str, b: str) -> bool:
    return _normalize_url(a) == _normalize_url(b)


def _normalize_address(address: str) -> str:
    without_units = _ADDRESS_UNIT_RE.sub(" ", address.casefold())
    words = re.sub(r"[^\w\s]", " ", without_units).split()
    expanded = [_ADDRESS_WORD_EXPANSIONS.get(word, word) for word in words]
    return " ".join(expanded)


def _addresses_match(a: str, b: str) -> bool:
    return _normalize_address(a) == _normalize_address(b)


def _geo_matches(a: GeoLocation, b: GeoLocation) -> bool:
    return (
        abs(a.latitude - b.latitude) <= _GEO_MATCH_DEGREES
        and abs(a.longitude - b.longitude) <= _GEO_MATCH_DEGREES
    )


def _has_matching_signal(keeper: Venue, candidate: Venue) -> bool:
    if _names_match(keeper.name, candidate.name):
        return True
    if keeper.url and candidate.url and _urls_match(keeper.url, candidate.url):
        return True
    if keeper.location and candidate.location and _addresses_match(keeper.location, candidate.location):
        return True
    if keeper.geo_location and candidate.geo_location and _geo_matches(keeper.geo_location, candidate.geo_location):
        return True
    return False


def _duplicate_groups(eligible: list[tuple[int, Venue]]) -> list[tuple[list[int], bool]]:
    valid_ids = {identifier for identifier, _ in eligible}
    prompt = _build_prompt(eligible)
    response = chat_completion([{"role": "user", "content": prompt}])
    data = _parse_json_object(response)

    raw_groups = data.get("groups")
    if not isinstance(raw_groups, list):
        return []

    groups: list[tuple[list[int], bool]] = []
    for raw_group in raw_groups:
        ids, ordered = _extract_ids(raw_group, valid_ids)
        if len(ids) < 2:
            continue
        groups.append((ids, ordered))
    return groups


def resolve_duplicate_venues(venues: list[Venue]) -> list[Venue]:
    eligible = [(i, venue) for i, venue in enumerate(venues) if venue.status == "accepted"]
    if len(eligible) < 2:
        return venues

    try:
        groups = _duplicate_groups(eligible)
    except Exception:
        return venues

    for ids, ordered in groups:
        candidates = [identifier for identifier in ids if venues[identifier].status == "accepted"]
        if len(candidates) < 2:
            continue

        keeper = candidates[0] if ordered else random.choice(candidates)
        keeper_venue = venues[keeper]
        for identifier in candidates:
            if identifier == keeper:
                continue
            candidate_venue = venues[identifier]
            if not _has_matching_signal(keeper_venue, candidate_venue):
                continue
            candidate_venue.status = "rejected"
            candidate_venue.rejection_reason = "duplicate"

    return venues
