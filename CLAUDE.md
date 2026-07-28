# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A trip-planning project (Python >=3.10,<3.14, managed with `uv`) that calls the OpenAI API directly via the `openai` SDK — no agent/task/crew framework. Venue search/lookup runs through `serper_places.py` / `serper_lookup.py` / `venue_processing.py`, and `openai_client.py` provides a small, direct wrapper around the OpenAI SDK for any AI-driven capability to call.

## Commands

```bash
uv sync                              # install/sync dependencies
uv run trip_planner                  # run the project (entry point: trip_planner.main:run)
uv run pytest                        # run the test suite
```

### Environment

`.env` requires `OPENAI_API_KEY` and `MODEL` (e.g. `gpt-4o-mini`) for `openai_client.py`, and `SERPER_API_KEY` for venue search/lookup.

## Architecture

- `src/trip_planner/openai_client.py` — reads `OPENAI_API_KEY` and `MODEL` from the environment and exposes a configured OpenAI SDK client plus a thin `chat_completion` helper for direct chat/completions calls.
- `src/trip_planner/main.py` — local entry point (`run`), builds a `TravelInfo` and calls `create_itinerary`. Keep this file free of business logic — it exists only to drive local execution.
- `knowledge/user_preference.txt` — sample knowledge source content; not currently wired into anything.
