import json

from trip_planner.integrations.openai_client import chat_completion

_RANKING_INSTRUCTIONS = (
    "Sort ALL of the candidate URLs below from most likely to least likely to be the "
    "venue's own official website. Prefer a URL that looks like the venue's own domain "
    "over social media profiles (e.g. Instagram, Facebook), review or directory/aggregator "
    "sites (e.g. Yelp, TripAdvisor, Google Maps listings), or otherwise unrelated pages. "
    "Every URL given below must appear exactly once in your answer.\n\n"
    "Respond with ONLY a JSON object with exactly one key, \"urls\", whose value is the "
    "list of candidate URLs sorted from most likely to least likely."
)


def _build_prompt(name: str, destination: str | None, results: list[dict]) -> str:
    lines = [f"Venue name: {name}"]
    if destination:
        lines.append(f"Destination: {destination}")
    lines.append("")
    lines.append("Candidates:")
    for result in results:
        link = result.get("link")
        if not link:
            continue
        snippet = result.get("snippet")
        lines.append(f"- URL: {link}")
        if snippet:
            lines.append(f"  Snippet: {snippet}")
    lines.append("")
    lines.append(_RANKING_INSTRUCTIONS)
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


def _validate_ranking(raw_urls: object, candidate_links: set[str]) -> list[str]:
    if not isinstance(raw_urls, list):
        return []

    validated: list[str] = []
    seen: set[str] = set()
    for entry in raw_urls:
        if not isinstance(entry, str):
            continue
        if entry not in candidate_links:
            continue
        if entry in seen:
            continue
        seen.add(entry)
        validated.append(entry)

    return validated


def rank_urls(name: str, destination: str | None, results: list[dict]) -> list[str]:
    candidate_links = {result["link"] for result in results if result.get("link")}
    if not candidate_links:
        return []

    prompt = _build_prompt(name, destination, results)
    response = chat_completion([{"role": "user", "content": prompt}])
    data = _parse_json_object(response)

    return _validate_ranking(data.get("urls"), candidate_links)
