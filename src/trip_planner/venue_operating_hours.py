import json
from dataclasses import dataclass

from trip_planner.openai_client import chat_completion

_WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_WEEKDAY_INDEX = {name: index for index, name in enumerate(_WEEKDAY_NAMES)}

_EXTRACTION_INSTRUCTIONS = (
    "Interpret the venue's hours of operation below and extract:\n\n"
    "open_time: the venue's typical daily opening time on the days it's open, in 24-hour "
    "HH:MM format. Use null if the venue is open 24 hours or no opening time is stated or "
    "implied.\n\n"
    "close_time: the venue's typical daily closing time on the days it's open, in 24-hour "
    "HH:MM format. Use null if the venue is open 24 hours or no closing time is stated or "
    "implied.\n\n"
    "closed_weekdays: a list of the full weekday names (e.g. \"Monday\") the venue is stated "
    "to be closed on. Use an empty list if no specific closed day(s) are stated.\n\n"
    "Respond with ONLY a JSON object with exactly these three keys: open_time, close_time, "
    "closed_weekdays."
)


@dataclass(frozen=True)
class OperatingHours:
    open_minutes: int | None = None
    close_minutes: int | None = None
    closed_weekdays: frozenset[int] = frozenset()

    def is_available(self, weekday: int | None, start_minutes: int, end_minutes: int) -> bool:
        if weekday is not None and weekday in self.closed_weekdays:
            return False
        if self.open_minutes is not None and start_minutes < self.open_minutes:
            return False
        has_reliable_close = self.close_minutes is not None and (
            self.open_minutes is None or self.close_minutes > self.open_minutes
        )
        if has_reliable_close and end_minutes > self.close_minutes:
            return False
        return True


_ALL_DAY = OperatingHours()


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


def _as_minutes(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    try:
        hours, minutes = value.strip().split(":")
        return int(hours) * 60 + int(minutes)
    except (ValueError, AttributeError):
        return None


def _as_closed_weekdays(value: object) -> frozenset[int]:
    if not isinstance(value, list):
        return frozenset()
    weekdays = set()
    for entry in value:
        if not isinstance(entry, str):
            continue
        index = _WEEKDAY_INDEX.get(entry.strip().title())
        if index is not None:
            weekdays.add(index)
    return frozenset(weekdays)


def parse_operating_hours(hours_of_operation: str | None) -> OperatingHours:
    if not hours_of_operation:
        return _ALL_DAY

    prompt = f"Hours of operation: {hours_of_operation}\n\n{_EXTRACTION_INSTRUCTIONS}"
    response = chat_completion([{"role": "user", "content": prompt}])
    data = _parse_json_object(response)

    return OperatingHours(
        open_minutes=_as_minutes(data.get("open_time")),
        close_minutes=_as_minutes(data.get("close_time")),
        closed_weekdays=_as_closed_weekdays(data.get("closed_weekdays")),
    )
