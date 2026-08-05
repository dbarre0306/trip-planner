# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A trip-planning project (Python >=3.10,<3.14, managed with `uv`) that calls the OpenAI API directly via the `openai` SDK — no agent/task/crew framework. Given a destination, dates, and a set of interests, it searches for venues, enriches each one (description, hours, duration, cost, meal suitability) via LLM calls, deduplicates them, and produces a list of `Venue`s. A Gradio app (`app.py`) provides a web UI on top of the same pipeline.

## Commands

```bash
uv sync                              # install/sync dependencies
uv run trip_planner                  # run the CLI entry point (trip_planner.main:run)
uv run app                           # launch the Gradio web UI (trip_planner.app:launch)
uv run pytest                        # run the full test suite
uv run pytest tests/test_venue_cost.py            # run one test file
uv run pytest tests/test_venue_cost.py -k somecase # run a single test by name
```

### Environment

`.env` requires `OPENAI_API_KEY` and `MODEL` (e.g. `gpt-4o-mini`) for `openai_client.py`, and `SERPER_API_KEY` for venue search/lookup (`serper_places.py`, `serper_lookup.py`).

## Architecture

### Domain model

- `domain.py` — static reference data and the core input type: `CategoryId`/`Category`, `InterestId`/`Interest` (each interest has a `search_text` used for venue search queries and belongs to a category), and `TravelInfo` (destination, dates, party size, chosen `interest_ids`).
- `models.py` — Pydantic types that flow through the pipeline: `VenueCandidate` (raw search hit) → `Venue` (fully enriched output, with `status: "accepted" | "rejected"` and a `rejection_reason` when rejected).

### Pipeline (`trip_planner.py` → `venue_processing.py`)

`create_itinerary(travel_info)` is the entry point:

1. `get_all_candidates` calls `serper_places.search_places` once per selected `interest_id` to get `VenueCandidate`s from the Serper Places API.
2. `venue_processing.process_venues` runs `process_venue` for every candidate concurrently (`ThreadPoolExecutor`). Each candidate is enriched into a `Venue` by chaining several independent, single-purpose modules, all built on `openai_client.chat_completion`:
   - `serper_lookup.lookup_venue` — web search for the venue, returns free-text `notes` plus a best-guess `url` (ranked via `venue_url_selection.rank_urls`).
   - `venue_description.generate_description` — LLM-written description from the notes.
   - `venue_details.extract_venue_details` — LLM-extracted structured facts (location, hours, closed status, duration) from the notes.
   - `venue_details.estimate_duration_minutes` — LLM fallback when duration isn't in the notes.
   - `venue_meal_tags.determine_meal_tags` — tags a venue breakfast/lunch/dinner for food-related interests.
   - `venue_cost.estimate_venue_cost` — LLM per-adult/per-child cost estimate.
   - A venue is rejected (`status="rejected"`) if it's closed or has no discoverable URL; see `_determine_status`.
3. Results are deduplicated (`venue_deduplication.resolve_duplicate_venues`, matching on name similarity and geo proximity) and merged with generic placeholder venues (`standard_venues.build_standard_venues`, e.g. "Breakfast"/"Lunch"/"Dinner" placeholders) that aren't tied to any interest.

Each enrichment module is independent and owns its own prompt — when changing one aspect of venue enrichment (e.g. cost estimation), only its module needs to change.

### Other entry points

- `main.py` — local CLI entry point (`run`), builds a `TravelInfo` and calls `create_itinerary`. Kept free of business logic — it exists only to drive local execution.
- `app.py` — application entry point (`launch`); builds the UI via `ui.build_ui()` and launches the Gradio server.
- `ui.py` — the Gradio UI itself: `build_ui()` lays out the form/results Blocks and wires up event handlers, exposing the same `create_itinerary` pipeline through a form; `validation.py` validates form input before submission, `assets.py` holds the UI's CSS/HTML.
- `knowledge/user_preference.txt` — sample knowledge source content; not currently wired into anything.

## Feature workflow

Non-trivial features go through a spec → plan → implement cycle, driven by the `/spec` and `/build-plan` skills (see `.claude/skills/`):

- `_specs/<feature>.md` — requirements for a feature, created by `/spec`.
- `_plans/<feature>.md` — implementation plan derived from a spec, created by `/build-plan`.
- `_templates/` — templates the two skills fill in.

Before starting new feature work, check `_specs/` and `_plans/` for an existing spec/plan pair on the topic.
