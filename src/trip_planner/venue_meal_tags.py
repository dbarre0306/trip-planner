import json

from trip_planner.domain import InterestId
from trip_planner.openai_client import chat_completion

_ELIGIBLE_INTERESTS = {InterestId.RESTAURANTS, InterestId.COFFEE_SHOPS, InterestId.STREET_FOOD}
_VALID_TAGS = {"breakfast", "lunch", "dinner"}
_FALLBACK_TAGS = ["lunch", "dinner"]

_INSTRUCTIONS = (
    "Determine which meal period(s) this venue is appropriate for: \"breakfast\", \"lunch\", "
    "and/or \"dinner\". A venue may serve more than one meal period.\n\n"
    "If the notes explicitly state which meal period(s) the venue serves or is known for, use "
    "those. Also weigh the hours of operation, if given, using these boundaries: breakfast "
    "starts anytime between 6am and 9am, lunch starts at 10am, and dinner starts at 4pm. A "
    "venue whose hours span multiple meal periods should be tagged with each period they "
    "span.\n\n"
    "If neither the notes nor the hours of operation indicate a meal period, give your best "
    "guess based on general knowledge of the type of venue.{restriction}\n\n"
    "Respond with ONLY a JSON object with exactly one key, \"meal_tags\", whose value is a list "
    "of one or more of \"breakfast\", \"lunch\", \"dinner\"."
)

_STREET_FOOD_RESTRICTION = (
    " This venue is a street food or market vendor, so it must never be tagged \"breakfast\" — "
    "only \"lunch\" and/or \"dinner\" apply."
)


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


def _build_prompt(
    name: str, notes: list[str], hours_of_operation: str | None, interest_id: InterestId
) -> str:
    lines = [f"Venue name: {name}"]
    if notes:
        lines.append("Notes:")
        lines.extend(f"- {note}" for note in notes)
    if hours_of_operation:
        lines.append(f"Hours of operation: {hours_of_operation}")
    lines.append("")
    restriction = _STREET_FOOD_RESTRICTION if interest_id == InterestId.STREET_FOOD else ""
    lines.append(_INSTRUCTIONS.format(restriction=restriction))
    return "\n".join(lines)


def _extract_tags(response: str, interest_id: InterestId) -> list[str]:
    data = _parse_json_object(response)
    raw_tags = data.get("meal_tags")

    tags: list[str] = []
    if isinstance(raw_tags, list):
        for entry in raw_tags:
            if not isinstance(entry, str):
                continue
            tag = entry.strip().casefold()
            if tag in _VALID_TAGS and tag not in tags:
                tags.append(tag)

    if interest_id == InterestId.STREET_FOOD:
        tags = [tag for tag in tags if tag != "breakfast"]

    return tags


def determine_meal_tags(
    interest_id: InterestId | None, name: str, notes: list[str], hours_of_operation: str | None
) -> list[str]:
    if interest_id not in _ELIGIBLE_INTERESTS:
        return []

    if interest_id == InterestId.COFFEE_SHOPS:
        return ["breakfast"]

    prompt = _build_prompt(name, notes, hours_of_operation, interest_id)
    response = chat_completion([{"role": "user", "content": prompt}])
    tags = _extract_tags(response, interest_id)

    return tags if tags else list(_FALLBACK_TAGS)
