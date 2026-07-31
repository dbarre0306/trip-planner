import json
from unittest.mock import patch

from trip_planner.domain import InterestId
from trip_planner.models import GeoLocation, Venue
from trip_planner.venue_deduplication import resolve_duplicate_venues


def _venue(name: str, **kwargs) -> Venue:
    return Venue(name=name, interest_id=kwargs.pop("interest_id", None), **kwargs)


@patch("trip_planner.venue_deduplication.chat_completion")
def test_resolve_duplicate_venues_includes_name_url_location_and_geo_in_prompt(mock_chat):
    mock_chat.return_value = json.dumps({"groups": []})
    venues = [
        _venue(
            "The Grand Hotel",
            url="https://grandhotel.example",
            location="123 Main St",
            geo_location=GeoLocation(latitude=1.0, longitude=2.0),
        ),
        _venue("Some Other Place", url="https://other.example"),
    ]

    resolve_duplicate_venues(venues)

    prompt = mock_chat.call_args[0][0][0]["content"]
    assert "The Grand Hotel" in prompt
    assert "https://grandhotel.example" in prompt
    assert "123 Main St" in prompt
    assert "1.0, 2.0" in prompt
    assert "Some Other Place" in prompt


@patch("trip_planner.venue_deduplication.chat_completion")
def test_resolve_duplicate_venues_keeps_most_specific_and_rejects_the_rest(mock_chat):
    venues = [
        _venue(
            "The Grand Hotel",
            url="https://grandhotel.example",
            location="500 Resort Way, Tucson, AZ",
        ),
        _venue(
            "The Grand Hotel Restaurant",
            url="https://grandhotelrestaurant.example",
            location="500 Resort Way, Tucson, AZ",
        ),
    ]
    mock_chat.return_value = json.dumps({"groups": [[1, 0]]})

    result = resolve_duplicate_venues(venues)

    assert result[1].status == "accepted"
    assert result[1].rejection_reason is None
    assert result[0].status == "rejected"
    assert result[0].rejection_reason == "duplicate"


@patch("trip_planner.venue_deduplication.chat_completion")
def test_resolve_duplicate_venues_ignores_interest_when_grouping(mock_chat):
    venues = [
        _venue("Sunset Bar", interest_id=InterestId.LIVE_MUSIC, url="https://sunsetbar.example"),
        _venue("Sunset Bar Rooftop", interest_id=InterestId.SCENIC_VIEWS, url="https://sunsetbar.example"),
    ]
    mock_chat.return_value = json.dumps({"groups": [[1, 0]]})

    result = resolve_duplicate_venues(venues)

    assert result[1].status == "accepted"
    assert result[0].status == "rejected"
    assert result[0].rejection_reason == "duplicate"


@patch("trip_planner.venue_deduplication.chat_completion")
def test_resolve_duplicate_venues_resolves_multi_way_duplicate_group(mock_chat):
    venues = [
        _venue("Place A", url="https://place.example"),
        _venue("Place B", url="https://place.example"),
        _venue("Place C", url="https://place.example"),
    ]
    mock_chat.return_value = json.dumps({"groups": [[2, 0, 1]]})

    result = resolve_duplicate_venues(venues)

    accepted = [v for v in result if v.status == "accepted"]
    rejected = [v for v in result if v.status == "rejected"]
    assert [v.name for v in accepted] == ["Place C"]
    assert {v.name for v in rejected} == {"Place A", "Place B"}
    assert all(v.rejection_reason == "duplicate" for v in rejected)


@patch("trip_planner.venue_deduplication.chat_completion")
def test_resolve_duplicate_venues_excludes_closed_venues_from_grouping_but_keeps_reason(mock_chat):
    venues = [
        _venue(
            "Closed Diner", url="https://diner.example", status="rejected", rejection_reason="closed"
        ),
        _venue("Diner Annex", url="https://diner.example/annex", location="200 W Main St"),
        _venue("Diner Take-Out Counter", url="https://diner.example/counter", location="200 W Main St"),
    ]
    mock_chat.return_value = json.dumps({"groups": [[2, 1]]})

    result = resolve_duplicate_venues(venues)

    prompt = mock_chat.call_args[0][0][0]["content"]
    assert "Closed Diner" not in prompt

    assert result[0].status == "rejected"
    assert result[0].rejection_reason == "closed"
    assert result[2].status == "accepted"
    assert result[1].status == "rejected"
    assert result[1].rejection_reason == "duplicate"


@patch("trip_planner.venue_deduplication.chat_completion")
def test_resolve_duplicate_venues_preserves_no_website_reason_over_duplicate(mock_chat):
    venues = [
        _venue("No Site Cafe", url=None, status="rejected", rejection_reason="no website"),
        _venue("Other Cafe", url="https://othercafe.example"),
    ]
    mock_chat.return_value = json.dumps({"groups": []})

    result = resolve_duplicate_venues(venues)

    assert result[0].status == "rejected"
    assert result[0].rejection_reason == "no website"
    assert result[1].status == "accepted"


@patch("trip_planner.venue_deduplication.chat_completion")
def test_resolve_duplicate_venues_drops_unknown_ids_from_group(mock_chat):
    venues = [
        _venue("Place A", url="https://place.example"),
        _venue("Place B", url="https://place.example"),
    ]
    mock_chat.return_value = json.dumps({"groups": [[0, 1, 99]]})

    result = resolve_duplicate_venues(venues)

    assert result[0].status == "accepted"
    assert result[1].status == "rejected"
    assert result[1].rejection_reason == "duplicate"


@patch("trip_planner.venue_deduplication.chat_completion")
def test_resolve_duplicate_venues_ignores_single_member_groups(mock_chat):
    venues = [
        _venue("Place A", url="https://place.example/a"),
        _venue("Place B", url="https://place.example/b"),
    ]
    mock_chat.return_value = json.dumps({"groups": [[0]]})

    result = resolve_duplicate_venues(venues)

    assert result[0].status == "accepted"
    assert result[1].status == "accepted"


@patch("trip_planner.venue_deduplication.random.choice")
@patch("trip_planner.venue_deduplication.chat_completion")
def test_resolve_duplicate_venues_falls_back_to_random_choice_when_order_is_unusable(
    mock_chat, mock_random_choice
):
    venues = [
        _venue("Place A", url="https://place.example"),
        _venue("Place B", url="https://place.example"),
    ]
    mock_chat.return_value = json.dumps({"groups": [{"first": 0, "second": 1}]})
    mock_random_choice.return_value = 1

    result = resolve_duplicate_venues(venues)

    mock_random_choice.assert_called_once()
    assert sorted(mock_random_choice.call_args[0][0]) == [0, 1]
    assert result[1].status == "accepted"
    assert result[0].status == "rejected"
    assert result[0].rejection_reason == "duplicate"


@patch("trip_planner.venue_deduplication.chat_completion")
def test_resolve_duplicate_venues_unordered_group_still_resolves_to_exactly_one_accepted(mock_chat):
    venues = [
        _venue("Place A", url="https://place.example"),
        _venue("Place B", url="https://place.example"),
    ]
    mock_chat.return_value = json.dumps({"groups": [{"first": 0, "second": 1}]})

    result = resolve_duplicate_venues(venues)

    accepted = [v for v in result if v.status == "accepted"]
    rejected = [v for v in result if v.status == "rejected"]
    assert len(accepted) == 1
    assert len(rejected) == 1
    assert rejected[0].rejection_reason == "duplicate"


@patch("trip_planner.venue_deduplication.chat_completion")
def test_resolve_duplicate_venues_ignores_group_without_a_real_matching_signal(mock_chat):
    venues = [
        _venue(
            "Culinary Dropout",
            url="https://www.culinarydropout.com/locations/tucson-az/",
            location="2543 E Grant Rd, Tucson, AZ 85716",
            geo_location=GeoLocation(latitude=32.250763, longitude=-110.93413),
        ),
        _venue(
            "La Frida Mexican Grill & Seafood",
            url="https://www.lafridamexicangrill.com/",
            location="7230 E 22nd St, Tucson, AZ 85705",
            geo_location=GeoLocation(latitude=32.20605, longitude=-110.83773),
        ),
    ]
    mock_chat.return_value = json.dumps({"groups": [[0, 1]]})

    result = resolve_duplicate_venues(venues)

    assert result[0].status == "accepted"
    assert result[1].status == "accepted"


@patch("trip_planner.venue_deduplication.chat_completion")
def test_resolve_duplicate_venues_skips_llm_call_when_fewer_than_two_eligible(mock_chat):
    venues = [
        _venue("Only Venue", url="https://only.example"),
        _venue("Closed Venue", url="https://closed.example", status="rejected", rejection_reason="closed"),
    ]

    result = resolve_duplicate_venues(venues)

    mock_chat.assert_not_called()
    assert result[0].status == "accepted"


@patch("trip_planner.venue_deduplication.chat_completion")
def test_resolve_duplicate_venues_leaves_venues_unchanged_when_llm_call_fails(mock_chat):
    mock_chat.side_effect = RuntimeError("boom")
    venues = [
        _venue("Place A", url="https://place.example/a"),
        _venue("Place B", url="https://place.example/b"),
    ]

    result = resolve_duplicate_venues(venues)

    assert result[0].status == "accepted"
    assert result[1].status == "accepted"


@patch("trip_planner.venue_deduplication.chat_completion")
def test_resolve_duplicate_venues_leaves_venues_unchanged_on_malformed_response(mock_chat):
    mock_chat.return_value = "not valid json"
    venues = [
        _venue("Place A", url="https://place.example/a"),
        _venue("Place B", url="https://place.example/b"),
    ]

    result = resolve_duplicate_venues(venues)

    assert result[0].status == "accepted"
    assert result[1].status == "accepted"
