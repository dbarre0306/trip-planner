# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A trip-planning project (Python >=3.10,<3.14, managed with `uv`) that calls the OpenAI API directly via the `openai` SDK — no agent/task/crew framework. Given a destination, dates, and a set of interests, it searches for venues, enriches each one (description, hours, duration, cost, meal suitability) via LLM calls, deduplicates them, and produces a list of `Venue`s. A Gradio app (`app.py`) is the only product surface and provides a web UI on top of the pipeline.

## Commands

```bash
uv sync                              # install/sync dependencies
uv run app                           # launch the Gradio web UI (trip_planner.app:launch)
uv run pytest                        # run the full test suite
uv run pytest tests/enrichment/test_venue_cost.py            # run one test file
uv run pytest tests/enrichment/test_venue_cost.py -k somecase # run a single test by name
```

### Environment

`.env` requires `OPENAI_API_KEY` and `MODEL` (e.g. `gpt-4o-mini`) for `integrations/openai_client.py`, and `SERPER_API_KEY` for venue search/lookup (`search/serper_places.py`, `enrichment/serper_lookup.py`).

## Architecture

`src/trip_planner/` is organized into subfolders by pipeline stage, with only the package `__init__.py` and the two top-level orchestration/entry files (`trip_planner.py`, `app.py`) living directly under it:

- `core/` — foundational domain and data types shared across every stage.
- `search/` — venue candidate discovery.
- `enrichment/` — per-venue enrichment.
- `consolidation/` — dedup and placeholder-venue merging.
- `scheduling/` — turning enriched venues into a day-by-day itinerary.
- `integrations/` — the shared OpenAI client used across stages.
- `ui/` — the Gradio UI.

### Core domain/data types (`core/`)

- `core/domain.py` — static reference data and the core input type: `CategoryId`/`Category`, `InterestId`/`Interest` (each interest has a `search_text` used for venue search queries and belongs to a category), and `TravelInfo` (destination, dates, party size, chosen `interest_ids`).
- `core/models.py` — Pydantic types that flow through the pipeline: `VenueCandidate` (raw search hit) → `Venue` (fully enriched output, with `status: "accepted" | "rejected"` and a `rejection_reason` when rejected).

### Pipeline (`trip_planner.py` → `enrichment/venue_processing.py`)

`create_itinerary(travel_info)` is the entry point:

1. `get_all_candidates` calls `search/serper_places.search_places` once per selected `interest_id` to get `VenueCandidate`s from the Serper Places API.
2. `enrichment/venue_processing.process_venues` runs `process_venue` for every candidate concurrently (`ThreadPoolExecutor`). Each candidate is enriched into a `Venue` by chaining several independent, single-purpose modules, all built on `integrations/openai_client.chat_completion`:
   - `enrichment/serper_lookup.lookup_venue` — web search for the venue, returns free-text `notes` plus a best-guess `url` (ranked via `enrichment/venue_url_selection.rank_urls`).
   - `enrichment/venue_description.generate_description` — LLM-written description from the notes.
   - `enrichment/venue_details.extract_venue_details` — LLM-extracted structured facts (location, hours, closed status, duration) from the notes.
   - `enrichment/venue_details.estimate_duration_minutes` — LLM fallback when duration isn't in the notes.
   - `enrichment/venue_meal_tags.determine_meal_tags` — tags a venue breakfast/lunch/dinner for food-related interests.
   - `enrichment/venue_cost.estimate_venue_cost` — LLM per-adult/per-child cost estimate.
   - A venue is rejected (`status="rejected"`) if it's closed or has no discoverable URL; see `_determine_status`.
3. Results are deduplicated (`consolidation/venue_deduplication.resolve_duplicate_venues`, matching on name similarity and geo proximity) and merged with generic placeholder venues (`consolidation/standard_venues.build_standard_venues`, e.g. "Breakfast"/"Lunch"/"Dinner" placeholders) that aren't tied to any interest.
4. `scheduling/itinerary.assemble_itinerary` lays the accepted venues out into a day-by-day schedule.

Each enrichment module is independent and owns its own prompt — when changing one aspect of venue enrichment (e.g. cost estimation), only its module needs to change.

### Other entry points

- `src/trip_planner/app.py` — application entry point (`launch`); stays at the top level of the package since it launches the app rather than belonging to one pipeline stage. Builds the UI via `ui/ui.build_ui()` and launches the Gradio server.
- `ui/ui.py` — the Gradio UI itself: `build_ui()` lays out the form/results Blocks and wires up event handlers, exposing the same `create_itinerary` pipeline through a form; `ui/validation.py` validates form input before submission, `ui/assets.py` holds the UI's CSS/HTML.
- `knowledge/user_preference.txt` — sample knowledge source content; not currently wired into anything.
- `app.py` (repo root) — the Hugging Face Space's `app_file`. Puts `src/` on `sys.path` and calls `trip_planner.app.launch`. Exists only because Spaces runs `app_file` as a bare script: if `app_file` pointed at `src/trip_planner/app.py` directly, Python would prepend that directory to `sys.path`, and the sibling `trip_planner.py` module would shadow the `trip_planner` package (`'trip_planner' is not a package`). Keep `app_file` in the README frontmatter pointed at this root shim, not the package-internal one.

## Feature workflow

Non-trivial features go through a spec → plan → implement cycle, driven by the `/spec` and `/build-plan` skills (see `.claude/skills/`):

- `_specs/<feature>.md` — requirements for a feature, created by `/spec`.
- `_plans/<feature>.md` — implementation plan derived from a spec, created by `/build-plan`.
- `_templates/` — templates the two skills fill in.

Before starting new feature work, check `_specs/` and `_plans/` for an existing spec/plan pair on the topic.
