import json
import re
from dataclasses import dataclass
from typing import Literal

from trip_planner.openai_client import chat_completion

DEFAULT_DURATION_MINUTES = 60

_INT_RE = re.compile(r"-?\d+")

_EXTRACTION_INSTRUCTIONS = (
    "Extract the following details about the venue using ONLY the notes below — do not "
    "invent or infer anything that isn't stated in the notes.\n\n"
    "location: If the notes contain a street address for the venue, use it. Otherwise, if "
    "the notes mention a distinct place or area the venue is situated within (e.g. a park, "
    "recreation area, or parent institution) that is not simply the venue's own name, use "
    "that place's name instead — for example, a museum wing should resolve to its parent "
    "museum, and a trail within a recreation area should resolve to the recreation area, not "
    "the trail's own name. Never use the venue name itself as the location. If neither can be "
    "found, use null.\n\n"
    "location_type: Classify the value you gave for location. Use \"STREET_ADDRESS\" if it is a "
    "street address, \"PLACE\" if it is a containing place or area name, or null if location "
    "itself is null.\n\n"
    "hours_of_operation: Use the hours exactly as stated in the notes, in whatever format they "
    "appear. If no hours are stated, use null.\n\n"
    "duration_minutes: If a duration or typical visit length is stated in the notes, convert "
    "it to a whole number of minutes. If no duration is stated, use null.\n\n"
    "closed: true only if the notes indicate the venue is not currently open to visitors, with "
    "no reopening indicated — for example \"permanently closed\", \"out of business\", or "
    "\"closed for the season\" with no reopening date given. A temporary closure with a "
    "specific reopening date or timeframe (e.g. \"closed for construction through Friday\") is "
    "still false, since the venue is expected to reopen. Also false when the notes merely "
    "describe a historic site as a ruin, abandoned homestead, or long-derelict structure — "
    "many trails and attractions lead to sites that are themselves ruins or abandoned "
    "buildings but remain open to visit today; being a ruin does not by itself mean the venue "
    "is closed. Also false when the word \"closed\" appears only as part of a weekly hours "
    "listing next to specific day(s) of the week (e.g. \"Mon - Closed, Tue - Closed, "
    "Wed-Sat 12pm-8pm\") — that describes the venue's normal days off, not the venue being shut "
    "down.\n\n"
    "Respond with ONLY a JSON object with exactly these five keys: location, location_type, "
    "hours_of_operation, duration_minutes, closed."
)

_DURATION_ESTIMATE_INSTRUCTIONS = (
    "Give your best estimate, in whole minutes, of how long a typical visit lasts. Rely only "
    "on your own general knowledge — do not use any external search. If you don't have "
    "specific knowledge of this exact venue, give a reasonable estimate based on the type of "
    "venue and comparable places. You must always provide a numeric estimate and must never "
    "decline to answer. Respond with ONLY the estimate as a whole number of minutes."
)


@dataclass(frozen=True)
class VenueDetails:
    location: str | None = None
    location_type: Literal["STREET_ADDRESS", "PLACE"] | None = None
    hours_of_operation: str | None = None
    duration_minutes: int | None = None
    closed: bool = False


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


def _as_optional_str(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _as_optional_location_type(value: object) -> Literal["STREET_ADDRESS", "PLACE"] | None:
    if value in ("STREET_ADDRESS", "PLACE"):
        return value
    return None


def _as_bool(value: object) -> bool:
    return value is True


def _as_optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, (float, str)):
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    return None


def _resolve_location(name: str, raw_location: str | None) -> str | None:
    if raw_location is None:
        return None
    if raw_location.strip().casefold() == name.strip().casefold():
        return None
    return raw_location


def extract_venue_details(name: str, notes: list[str]) -> VenueDetails:
    if not notes:
        return VenueDetails()

    notes_text = "\n".join(f"- {note}" for note in notes)
    prompt = f"Venue name: {name}\n\nNotes:\n{notes_text}\n\n{_EXTRACTION_INSTRUCTIONS}"

    response = chat_completion([{"role": "user", "content": prompt}])
    data = _parse_json_object(response)

    location = _resolve_location(name, _as_optional_str(data.get("location")))
    location_type = _as_optional_location_type(data.get("location_type")) if location else None

    return VenueDetails(
        location=location,
        location_type=location_type,
        hours_of_operation=_as_optional_str(data.get("hours_of_operation")),
        duration_minutes=_as_optional_int(data.get("duration_minutes")),
        closed=_as_bool(data.get("closed")),
    )


def estimate_duration_minutes(name: str, location: str | None) -> int:
    context = f"Venue name: {name}"
    if location:
        context += f"\nLocation: {location}"
    prompt = f"{context}\n\n{_DURATION_ESTIMATE_INSTRUCTIONS}"

    response = chat_completion([{"role": "user", "content": prompt}])
    match = _INT_RE.search(response)
    return int(match.group()) if match else DEFAULT_DURATION_MINUTES
