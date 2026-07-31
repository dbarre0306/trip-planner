import json
from dataclasses import dataclass

from trip_planner.domain import InterestId, find_interest_by_id
from trip_planner.openai_client import chat_completion

_COST_ESTIMATE_INSTRUCTIONS = (
    "Estimate the typical out-of-pocket cost, in USD, for one adult and for one child to visit "
    "this venue (e.g. admission, ticket, or cover price). Rely on your own general knowledge of "
    "typical pricing for this destination and type of venue, combined with the context below. "
    "Use 0 if the venue is free to enter. Use null for a field only if you have no reasonably "
    "reliable basis for an estimate — never guess wildly.\n\n"
    "Respond with ONLY a JSON object with exactly these two keys: cost_per_adult, cost_per_child."
)


@dataclass(frozen=True)
class VenueCost:
    per_adult: float | None = None
    per_child: float | None = None


def _format_context(
    name: str,
    interest_id: InterestId | None,
    destination: str | None,
    description: str,
    tags: list[str],
) -> str:
    lines = [f"Venue name: {name}"]
    if interest_id:
        interest = find_interest_by_id(interest_id)
        if interest:
            lines.append(f"Interest category: {interest.search_text}")
    if destination:
        lines.append(f"Destination: {destination}")
    if description:
        lines.append(f"Description: {description}")
    if tags:
        lines.append(f"Tags: {', '.join(tags)}")
    return "\n".join(lines)


def _build_prompt(
    name: str,
    interest_id: InterestId | None,
    destination: str | None,
    description: str,
    notes: list[str],
    tags: list[str],
) -> str:
    context = _format_context(name, interest_id, destination, description, tags)
    if notes:
        notes_text = "\n".join(f"- {note}" for note in notes)
        context += f"\nNotes:\n{notes_text}"
    return f"{context}\n\n{_COST_ESTIMATE_INSTRUCTIONS}"


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


def _as_optional_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def estimate_venue_cost(
    name: str,
    interest_id: InterestId | None,
    destination: str | None,
    description: str,
    notes: list[str],
    tags: list[str],
) -> VenueCost:
    prompt = _build_prompt(name, interest_id, destination, description, notes, tags)
    response = chat_completion([{"role": "user", "content": prompt}])
    data = _parse_json_object(response)

    return VenueCost(
        per_adult=_as_optional_float(data.get("cost_per_adult")),
        per_child=_as_optional_float(data.get("cost_per_child")),
    )
