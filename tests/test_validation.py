from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from trip_planner.validation import is_valid_destination, validate_form


def _valid_args(**overrides):
    args = dict(
        destination="Tucson, AZ",
        start_date=date.today() + timedelta(days=1),
        num_days=3,
        num_adults=2,
        num_children=0,
    )
    args.update(overrides)
    return args


def test_validate_form_returns_no_errors_for_valid_input():
    errors, err_fields = validate_form(**_valid_args())

    assert errors == []
    assert err_fields == set()


def test_validate_form_requires_destination():
    errors, err_fields = validate_form(**_valid_args(destination=""))

    assert "Destination is required" in errors
    assert "destination" in err_fields


def test_validate_form_rejects_blank_destination():
    errors, err_fields = validate_form(**_valid_args(destination="   "))

    assert "Destination is required" in errors
    assert "destination" in err_fields


def test_validate_form_requires_start_date():
    errors, err_fields = validate_form(**_valid_args(start_date=None))

    assert "Start date is required" in errors
    assert "start_date" in err_fields


def test_validate_form_rejects_past_start_date():
    errors, err_fields = validate_form(**_valid_args(start_date=date.today() - timedelta(days=1)))

    assert "Start date cannot be in the past" in errors
    assert "start_date" in err_fields


def test_validate_form_accepts_todays_start_date():
    errors, err_fields = validate_form(**_valid_args(start_date=date.today()))

    assert errors == []
    assert "start_date" not in err_fields


def test_validate_form_accepts_start_date_as_datetime():
    tomorrow = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())
    errors, err_fields = validate_form(**_valid_args(start_date=tomorrow))

    assert errors == []
    assert "start_date" not in err_fields


def test_validate_form_rejects_past_start_date_as_timestamp():
    past = datetime.combine(date.today() - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    errors, err_fields = validate_form(**_valid_args(start_date=past.timestamp()))

    assert "Start date cannot be in the past" in errors
    assert "start_date" in err_fields


def test_validate_form_accepts_future_start_date_as_timestamp():
    future = datetime.combine(date.today() + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    errors, err_fields = validate_form(**_valid_args(start_date=future.timestamp()))

    assert errors == []
    assert "start_date" not in err_fields


def test_validate_form_rejects_zero_days():
    errors, err_fields = validate_form(**_valid_args(num_days=0))

    assert "Days must be between 1 and 4" in errors
    assert "num_days" in err_fields


def test_validate_form_rejects_missing_days():
    errors, err_fields = validate_form(**_valid_args(num_days=None))

    assert "Days must be between 1 and 4" in errors
    assert "num_days" in err_fields


def test_validate_form_rejects_too_many_days():
    errors, err_fields = validate_form(**_valid_args(num_days=5))

    assert "Days must be between 1 and 4" in errors
    assert "num_days" in err_fields


def test_validate_form_accepts_boundary_days():
    errors, err_fields = validate_form(**_valid_args(num_days=4))

    assert errors == []
    assert "num_days" not in err_fields


def test_validate_form_rejects_zero_adults():
    errors, err_fields = validate_form(**_valid_args(num_adults=0))

    assert "Adults must be at least 1" in errors
    assert "num_adults" in err_fields


def test_validate_form_rejects_too_many_adults():
    errors, err_fields = validate_form(**_valid_args(num_adults=11))

    assert "Adults cannot exceed 10" in errors
    assert "num_adults" in err_fields


def test_validate_form_accepts_boundary_adults():
    errors, err_fields = validate_form(**_valid_args(num_adults=10))

    assert errors == []
    assert "num_adults" not in err_fields


def test_validate_form_rejects_negative_children():
    errors, err_fields = validate_form(**_valid_args(num_children=-1))

    assert "Children cannot be negative" in errors
    assert "num_children" in err_fields


def test_validate_form_rejects_missing_children():
    errors, err_fields = validate_form(**_valid_args(num_children=None))

    assert "Children cannot be negative" in errors
    assert "num_children" in err_fields


def test_validate_form_rejects_too_many_children():
    errors, err_fields = validate_form(**_valid_args(num_children=11))

    assert "Children cannot exceed 10" in errors
    assert "num_children" in err_fields


def test_validate_form_accepts_boundary_children():
    errors, err_fields = validate_form(**_valid_args(num_children=10))

    assert errors == []
    assert "num_children" not in err_fields


def test_validate_form_accepts_zero_children():
    errors, err_fields = validate_form(**_valid_args(num_children=0))

    assert errors == []
    assert "num_children" not in err_fields


def test_validate_form_collects_multiple_errors():
    errors, err_fields = validate_form(
        destination="", start_date=None, num_days=0, num_adults=0, num_children=-1
    )

    assert len(errors) == 5
    assert err_fields == {"destination", "start_date", "num_days", "num_adults", "num_children"}


@patch("trip_planner.validation.chat_completion", return_value="Yes")
def test_is_valid_destination_returns_true_for_yes(mock_chat_completion):
    assert is_valid_destination("Tucson, AZ") is True


@patch("trip_planner.validation.chat_completion", return_value="No")
def test_is_valid_destination_returns_false_for_no(mock_chat_completion):
    assert is_valid_destination("Asdkjaslkdj") is False


@patch("trip_planner.validation.chat_completion", return_value="  YES.  ")
def test_is_valid_destination_is_case_insensitive_and_trims_whitespace(mock_chat_completion):
    assert is_valid_destination("Tucson, AZ") is True


@patch("trip_planner.validation.chat_completion", return_value="yes")
def test_is_valid_destination_sends_expected_prompt(mock_chat_completion):
    is_valid_destination("Paris")

    (messages,), _ = mock_chat_completion.call_args
    assert "Paris" in messages[0]["content"]
