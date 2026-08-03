from trip_planner.openai_client import chat_completion

MAX_DESCRIPTION_LENGTH = 300

_TONE_INSTRUCTION = (
    "Write a single short, fun and imaginative description of this placeholder stop that "
    "would make a traveler smile and look forward to it, even though no specific venue has "
    "been picked yet."
)
_EXCLUSION_INSTRUCTION = (
    "Do not include any URL, website reference, physical address or location, "
    "or hours of operation."
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
