from datetime import date, datetime, timezone

from trip_planner.openai_client import chat_completion


def validate_form(
    destination: str | None,
    start_date,
    num_days: float | None,
    num_adults: float | None,
    num_children: float | None,
) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    err_fields: set[str] = set()

    if not (destination or "").strip():
        errors.append("Destination is required")
        err_fields.add("destination")

    if start_date is None:
        errors.append("Start date is required")
        err_fields.add("start_date")
    else:
        if isinstance(start_date, (int, float)):
            picked = datetime.fromtimestamp(start_date, tz=timezone.utc).date()
        elif hasattr(start_date, "date"):
            picked = start_date.date()
        else:
            picked = start_date if isinstance(start_date, date) else None
        if picked is not None and picked < date.today():
            errors.append("Start date cannot be in the past")
            err_fields.add("start_date")

    if not num_days or num_days < 1:
        errors.append("Days must be at least 1")
        err_fields.add("num_days")
    elif num_days > 10:
        errors.append("Days cannot exceed 10")
        err_fields.add("num_days")

    if not num_adults or num_adults < 1:
        errors.append("Adults must be at least 1")
        err_fields.add("num_adults")
    elif num_adults > 8:
        errors.append("Adults cannot exceed 8")
        err_fields.add("num_adults")

    if num_children is None or num_children < 0:
        errors.append("Children cannot be negative")
        err_fields.add("num_children")
    elif num_children > 8:
        errors.append("Children cannot exceed 8")
        err_fields.add("num_children")

    return errors, err_fields


def is_valid_destination(destination: str) -> bool:
    answer = chat_completion(
        [
            {
                "role": "user",
                "content": (
                    f'Is "{destination}" a real, recognisable travel destination? '
                    'Answer with only "yes" or "no".'
                ),
            }
        ]
    )
    return answer.strip().lower().startswith("yes")
