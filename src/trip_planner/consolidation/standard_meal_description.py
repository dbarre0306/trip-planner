from trip_planner.integrations.openai_client import chat_completion

MAX_DESCRIPTION_LENGTH = 300

_TONE_INSTRUCTION = (
    "Write a single short, fun and imaginative description of this placeholder stop that "
    "would make a traveler smile and look forward to it, even though no specific venue has "
    "been picked yet. Phrase it as a hypothetical rather than describing it as if it were a "
    "real place that already exists — for example, write 'Imagine a delightful lunch stop "
    "with a treasure trove of flavors!' rather than 'Nestled among the lively streets of the "
    "city, this delightful lunch stop is a treasure trove of flavors!'. Vary the opening word "
    "or phrase each time instead of always starting with 'Imagine' — mix in openers like "
    "'Picture', 'Enjoy', 'Savor', 'Treat yourself to', 'Get ready for', or similar."
)
_EXCLUSION_INSTRUCTION = (
    "Do not include any URL, website reference, physical address or location, "
    "or hours of operation. Do not name or reference any actual, real, or specific "
    "restaurant, cafe, or venue, whether real or invented — describe only the generic "
    "experience of the meal. Do not use scene-setting or grounding phrases (such as "
    "'nestled among', 'in the heart of', 'tucked away in', or naming the destination's "
    "streets or neighborhoods) that imply the description refers to an actual, real place — "
    "the destination should at most flavor the imagined cuisine or vibe, never the setting."
)
_LENGTH_INSTRUCTION = f"Keep the description under {MAX_DESCRIPTION_LENGTH} characters."


def generate_standard_meal_description(meal: str, destination: str | None) -> str:
    context = f"This is a generic placeholder venue for {meal} during a trip"
    if destination:
        context += f" to {destination}"
    context += "."

    prompt = f"{context}\n\n{_TONE_INSTRUCTION} {_EXCLUSION_INSTRUCTION} {_LENGTH_INSTRUCTION}"

    description = chat_completion([{"role": "user", "content": prompt}])
    return description.strip()
