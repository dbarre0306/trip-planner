import re

from trip_planner.domain import InterestId, find_interest_by_id
from trip_planner.openai_client import chat_completion

MAX_DESCRIPTION_LENGTH = 300

_SENTENCE_END_RE = re.compile(r"[.!?](?=\s|$)")

_TONE_INSTRUCTION = (
    "Write in an engaging, inviting tone that would appeal to a tourist deciding "
    "whether to visit."
)
_EXCLUSION_INSTRUCTION = (
    "Do not include any URL, website reference, physical address or location, "
    "or hours of operation."
)
_LENGTH_INSTRUCTION = (
    f"Keep the description under {MAX_DESCRIPTION_LENGTH} characters. "
    "Do NOT truncate or cutoff the last sentence before its end."
)


def _format_context(name: str, interest_id: InterestId | None, destination: str | None) -> str:
    lines = [f"Venue name: {name}"]
    if interest_id:
        interest = find_interest_by_id(interest_id)
        if interest:
            lines.append(f"Interest category: {interest.search_text}")
    if destination:
        lines.append(f"Destination: {destination}")
    return "\n".join(lines)


def _build_notes_prompt(
    name: str, interest_id: InterestId | None, destination: str | None, notes: list[str]
) -> str:
    notes_text = "\n".join(f"- {note}" for note in notes)
    context = _format_context(name, interest_id, destination)
    return (
        "Write a single short description of the venue below, based primarily on "
        "the notes. Use the venue name, interest category, and destination only as "
        "light supporting context to disambiguate or ground the description — do "
        "not treat them as the main source.\n\n"
        f"Notes:\n{notes_text}\n\n"
        f"Context:\n{context}\n\n"
        f"{_TONE_INSTRUCTION} {_EXCLUSION_INSTRUCTION} {_LENGTH_INSTRUCTION}"
    )


def _build_fallback_prompt(name: str, interest_id: InterestId | None, destination: str | None) -> str:
    context = _format_context(name, interest_id, destination)
    return (
        "No notes are available for this venue. Write a single short, cool and "
        "meaningful description based only on the venue name, interest category, "
        "and destination below.\n\n"
        f"{context}\n\n"
        f"{_TONE_INSTRUCTION} {_EXCLUSION_INSTRUCTION} {_LENGTH_INSTRUCTION}"
    )


# in case the LLM did cutoff of the last sentence mid-stream.  
# we'll throw away that sentence.
def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text

    truncated = text[:max_length]
    sentence_ends = list(_SENTENCE_END_RE.finditer(truncated))
    if sentence_ends:
        return truncated[: sentence_ends[-1].end()]

    word_boundary = truncated.rfind(" ")
    if word_boundary > 0:
        return truncated[:word_boundary].rstrip()
    return truncated


def generate_description(
    name: str,
    interest_id: InterestId | None,
    destination: str | None,
    notes: list[str],
) -> str:
    if notes:
        prompt = _build_notes_prompt(name, interest_id, destination, notes)
    else:
        prompt = _build_fallback_prompt(name, interest_id, destination)

    description = chat_completion([{"role": "user", "content": prompt}])
    return _truncate(description.strip(), MAX_DESCRIPTION_LENGTH)
