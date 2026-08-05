import re
from dataclasses import dataclass, field
from datetime import datetime

from trip_planner.core.domain import CATEGORIES, TravelInfo, find_interest_by_id
from trip_planner.core.models import Itinerary, ItineraryDay, ScheduledVenue, Venue
from trip_planner.consolidation.standard_meal_description import generate_standard_meal_description
from trip_planner.consolidation.venue_geo_clustering import cluster_venues
from trip_planner.enrichment.venue_operating_hours import OperatingHours, parse_operating_hours

_MIN_GAP_MINUTES = 60
_DEFAULT_DURATION_MINUTES = 60
_DAY_START_MINUTES = 6 * 60
_DAY_END_MINUTES = 22 * 60
_MEAL_MIN_DURATION_MINUTES = {"dinner": 120}

_MEAL_WINDOWS = {
    "breakfast": (6 * 60, 9 * 60),
    "lunch": (11 * 60, 13 * 60),
    "dinner": (17 * 60, 20 * 60),
}
_MEAL_ANCHORS = {
    "breakfast": 8 * 60,
    "lunch": 12 * 60,
    "dinner": 18 * 60,
}
_MEAL_TAGS = frozenset(_MEAL_WINDOWS)

_PRECEDING_SEGMENT = {"breakfast": None, "lunch": "seg1", "dinner": "seg2"}

_SEGMENT_ORDER = ["breakfast", "seg1", "lunch", "seg2", "dinner", "seg3"]

_CATEGORY_LABELS = {category.id: category.label for category in CATEGORIES}
_FALLBACK_CATEGORY_LABEL = "Food & Drinks"


def _duration(venue: Venue, meal: str | None = None) -> int:
    base = venue.duration_minutes if venue.duration_minutes is not None else _DEFAULT_DURATION_MINUTES
    minimum = _MEAL_MIN_DURATION_MINUTES.get(meal)
    return max(base, minimum) if minimum is not None else base


def _category_label(venue: Venue) -> str:
    if venue.interest_id is None:
        return _FALLBACK_CATEGORY_LABEL
    interest = find_interest_by_id(venue.interest_id)
    if interest is None:
        return _FALLBACK_CATEGORY_LABEL
    return _CATEGORY_LABELS.get(interest.category_id, _FALLBACK_CATEGORY_LABEL)


def _format_time(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _clamp_to_window(value: int, meal: str) -> int:
    window_start, window_end = _MEAL_WINDOWS[meal]
    return min(max(value, window_start), window_end)


def _weekday_for_date(date: str) -> int | None:
    try:
        return datetime.strptime(date, "%Y-%m-%d").weekday()
    except ValueError:
        return None


def _total_cost(venue: Venue, num_adults: int, num_children: int) -> float:
    per_adult = venue.estimated_cost_per_adult or 0
    per_child = venue.estimated_cost_per_child or 0
    return per_adult * num_adults + per_child * num_children


def _venue_identity(venue: Venue) -> str:
    """A key identifying the real-world place a venue represents.

    Used to keep the same place from being scheduled on more than one day, even when
    it's represented by more than one `Venue` object (e.g. a duplicate that slipped
    past the earlier LLM-based duplicate-merging step).
    """
    return re.sub(r"\s+", " ", venue.name).strip().casefold()


@dataclass
class _Segment:
    boundary_end: int
    entries: list[tuple[int, Venue]] = field(default_factory=list)


@dataclass
class _DaySchedule:
    day_number: int
    date: str
    breakfast: tuple[int, Venue] | None = None
    lunch: tuple[int, Venue] | None = None
    dinner: tuple[int, Venue] | None = None
    seg1: _Segment = field(
        default_factory=lambda: _Segment(_MEAL_WINDOWS["lunch"][1] - _MIN_GAP_MINUTES)
    )
    seg2: _Segment = field(
        default_factory=lambda: _Segment(_MEAL_WINDOWS["dinner"][1] - _MIN_GAP_MINUTES)
    )
    seg3: _Segment = field(default_factory=lambda: _Segment(_DAY_END_MINUTES))

    def all_entries(self) -> list[tuple[int, Venue]]:
        result: list[tuple[int, Venue]] = []
        for name in _SEGMENT_ORDER:
            if name in ("breakfast", "lunch", "dinner"):
                slot = getattr(self, name)
                if slot is not None:
                    result.append(slot)
            else:
                result.extend(getattr(self, name).entries)
        return result

    def segment_cursor(self, name: str) -> int:
        idx = _SEGMENT_ORDER.index(name)
        entries: list[tuple[int, Venue]] = []
        for n in _SEGMENT_ORDER[: idx + 1]:
            if n in ("breakfast", "lunch", "dinner"):
                slot = getattr(self, n)
                if slot is not None:
                    entries.append(slot)
            else:
                entries.extend(getattr(self, n).entries)
        if not entries:
            return _DAY_START_MINUTES
        start, venue = entries[-1]
        return start + _duration(venue) + _MIN_GAP_MINUTES

    @property
    def total_duration(self) -> int:
        return sum(_duration(venue) for _, venue in self.all_entries())

    @property
    def used_interests(self) -> set:
        return {venue.interest_id for _, venue in self.all_entries() if venue.interest_id is not None}


def _select_meal_venue(
    pool: list[Venue],
    used: set[str],
    operating_hours: dict[int, OperatingHours],
    weekday: int | None,
    start_minutes: int,
    meal: str,
) -> Venue | None:
    candidates = [
        venue
        for venue in pool
        if _venue_identity(venue) not in used
        and operating_hours[id(venue)].is_available(
            weekday, start_minutes, start_minutes + _duration(venue, meal)
        )
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda venue: venue.rating if venue.rating is not None else -1)


def _standard_venue(accepted: list[Venue], meal: str) -> Venue | None:
    return next((venue for venue in accepted if venue.origin == "standard" and meal in venue.tags), None)


def _standard_copy(base: Venue, destination: str | None, meal: str) -> Venue:
    description = generate_standard_meal_description(meal, destination)
    return base.model_copy(deep=True, update={"description": description})


def _schedule_meal(
    day: _DaySchedule,
    meal: str,
    pool: list[Venue],
    used: set[str],
    accepted: list[Venue],
    destination: str | None,
    operating_hours: dict[int, OperatingHours],
    weekday: int | None,
) -> None:
    start = _clamp_to_window(max(_MEAL_ANCHORS[meal], day.segment_cursor(meal)), meal)

    venue = _select_meal_venue(pool, used, operating_hours, weekday, start, meal)
    if venue is not None:
        used.add(_venue_identity(venue))
    else:
        base = _standard_venue(accepted, meal)
        if base is None:
            return
        venue = _standard_copy(base, destination, meal)

    effective_duration = _duration(venue, meal)
    if meal in _MEAL_MIN_DURATION_MINUTES and venue.duration_minutes != effective_duration:
        venue = venue.model_copy(update={"duration_minutes": effective_duration})

    setattr(day, meal, (start, venue))

    preceding_segment_name = _PRECEDING_SEGMENT[meal]
    if preceding_segment_name is not None:
        segment = getattr(day, preceding_segment_name)
        segment.boundary_end = min(segment.boundary_end, start - _MIN_GAP_MINUTES)


def _pick_next_activity(candidates: list[Venue], used_interests: set) -> Venue:
    fresh = [venue for venue in candidates if venue.interest_id not in used_interests]
    pick_from = fresh if fresh else candidates
    return max(pick_from, key=lambda venue: venue.rating if venue.rating is not None else -1)


def _fill_segment(
    day: _DaySchedule,
    name: str,
    cluster_pool: list[Venue],
    used: set[str],
    operating_hours: dict[int, OperatingHours],
    weekday: int | None,
) -> None:
    segment = getattr(day, name)
    while True:
        cursor = day.segment_cursor(name)
        candidates = [
            venue
            for venue in cluster_pool
            if _venue_identity(venue) not in used
            and cursor + _duration(venue) <= segment.boundary_end
            and operating_hours[id(venue)].is_available(weekday, cursor, cursor + _duration(venue))
        ]
        if not candidates:
            break
        chosen = _pick_next_activity(candidates, day.used_interests)
        segment.entries.append((cursor, chosen))
        used.add(_venue_identity(chosen))


def _try_place(
    day: _DaySchedule,
    venue: Venue,
    name: str,
    operating_hours: dict[int, OperatingHours],
    weekday: int | None,
) -> bool:
    segment = getattr(day, name)
    cursor = day.segment_cursor(name)
    if cursor + _duration(venue) > segment.boundary_end:
        return False
    if not operating_hours[id(venue)].is_available(weekday, cursor, cursor + _duration(venue)):
        return False
    segment.entries.append((cursor, venue))
    return True


def _assemble_day(
    day_number: int,
    date: str,
    destination: str | None,
    accepted: list[Venue],
    cluster_pool: list[Venue],
    pools: dict[str, list[Venue]],
    used: set[str],
    operating_hours: dict[int, OperatingHours],
) -> _DaySchedule:
    day = _DaySchedule(day_number=day_number, date=date)
    weekday = _weekday_for_date(date)

    _schedule_meal(day, "breakfast", pools["breakfast"], used, accepted, destination, operating_hours, weekday)
    _fill_segment(day, "seg1", cluster_pool, used, operating_hours, weekday)
    _schedule_meal(day, "lunch", pools["lunch"], used, accepted, destination, operating_hours, weekday)
    _fill_segment(day, "seg2", cluster_pool, used, operating_hours, weekday)
    _schedule_meal(day, "dinner", pools["dinner"], used, accepted, destination, operating_hours, weekday)
    _fill_segment(day, "seg3", cluster_pool, used, operating_hours, weekday)

    return day


def _rebalance(
    days: list[_DaySchedule],
    leftover: list[Venue],
    used: set[str],
    operating_hours: dict[int, OperatingHours],
) -> None:
    progress = True
    while progress and leftover:
        progress = False
        for day in sorted(days, key=lambda d: d.total_duration):
            weekday = _weekday_for_date(day.date)
            used_interests = day.used_interests
            ranked = sorted(
                leftover,
                key=lambda venue: (
                    venue.interest_id in used_interests,
                    -(venue.rating if venue.rating is not None else -1),
                ),
            )
            for venue in ranked:
                if any(
                    _try_place(day, venue, name, operating_hours, weekday)
                    for name in ("seg1", "seg2", "seg3")
                ):
                    used.add(_venue_identity(venue))
                    leftover.remove(venue)
                    progress = True
                    break
            if progress:
                break


def _to_scheduled(venue: Venue, start_minutes: int, num_adults: int, num_children: int) -> ScheduledVenue:
    return ScheduledVenue(
        name=venue.name,
        interest_category=_category_label(venue),
        description=venue.description,
        rating=venue.rating,
        location=venue.location,
        location_type=venue.location_type,
        geo_location=venue.geo_location,
        hours_of_operation=venue.hours_of_operation,
        url=venue.url,
        start_time=_format_time(start_minutes),
        duration_minutes=_duration(venue),
        estimated_cost_usd=_total_cost(venue, num_adults, num_children),
    )


def assemble_itinerary(travel_info: TravelInfo, venues: list[Venue]) -> Itinerary:
    if not travel_info.travel_dates:
        return Itinerary(
            destination=travel_info.destination,
            num_adults=travel_info.num_adults,
            num_children=travel_info.num_children,
            days=[],
        )

    accepted = [venue for venue in venues if venue.status == "accepted"]
    non_standard = [venue for venue in accepted if venue.origin != "standard"]

    pools = {
        meal: [venue for venue in non_standard if meal in venue.tags] for meal in _MEAL_WINDOWS
    }
    activity_pool = [venue for venue in non_standard if not (_MEAL_TAGS & set(venue.tags))]

    operating_hours = {id(venue): parse_operating_hours(venue.hours_of_operation) for venue in accepted}

    num_days = len(travel_info.travel_dates)
    clusters = cluster_venues(activity_pool, num_days)

    used: set[str] = set()
    days: list[_DaySchedule] = []
    for day_number, date in enumerate(travel_info.travel_dates, start=1):
        cluster_pool = clusters[day_number - 1] if day_number - 1 < len(clusters) else []
        day = _assemble_day(
            day_number, date, travel_info.destination, accepted, cluster_pool, pools, used, operating_hours
        )
        days.append(day)

    leftover = [venue for venue in activity_pool if _venue_identity(venue) not in used]
    _rebalance(days, leftover, used, operating_hours)

    return Itinerary(
        destination=travel_info.destination,
        num_adults=travel_info.num_adults,
        num_children=travel_info.num_children,
        days=[
            ItineraryDay(
                day_number=day.day_number,
                date=day.date,
                venues=[
                    _to_scheduled(venue, start, travel_info.num_adults, travel_info.num_children)
                    for start, venue in day.all_entries()
                ],
            )
            for day in days
        ],
    )
