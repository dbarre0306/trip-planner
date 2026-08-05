# Plan: Reorganize Source Code Into Folders

spec: _specs/reorganize-source-code-into-folders.md

## Summary

`src/trip_planner/` currently holds 24 Python modules as a flat list with no subfolders, and `tests/` mirrors that flat layout with 20 test files. This plan regroups the source modules into subfolders by pipeline stage — core domain/data types, venue search, per-venue enrichment, dedup/consolidation, itinerary scheduling, external integrations, and the UI — leaving only the package `__init__.py` and the two top-level orchestration/entry files (`trip_planner.py`, `app.py`) directly under `src/trip_planner/`. Test files move into a matching subfolder structure. No behavior, prompts, or UI change; only import paths, file locations, and documentation that references them are updated.

## Assumptions

- The domain/data-types folder is named `core/` rather than `domain/`, since `domain.py` would otherwise sit inside a folder also named `domain`, producing a confusing `trip_planner.domain.domain` import path. `core/` matches the spec's own wording ("core domain/data types").
- `trip_planner.py` (the `create_itinerary`/`get_all_candidates` orchestrator) and `app.py` (the Gradio launch entry point) stay directly under `src/trip_planner/` rather than moving into a subfolder — they each tie multiple pipeline stages together (or launch the app) rather than belonging to one stage, and keeping them at the top level means `pyproject.toml`'s `app = "trip_planner.app:launch"` script entry does not need to change.
- No module is renamed and no logic is changed — this is purely a file-move plus import-path update. `ui.py` keeps its name even though it now lives under a folder also named `ui` (`trip_planner.ui.ui`); this is consistent with the `core/` exception above being the one deliberate naming carve-out.
- `standard_venues.py` and `standard_meal_description.py` are grouped under `consolidation/` (alongside dedup) rather than `enrichment/`, since they build/merge fallback placeholder venues after enrichment rather than enriching a single candidate.
- Test files move to mirror their source module's new folder, keeping their existing filenames; `tests/test_trip_planner.py` stays directly under `tests/` to mirror `trip_planner.py` staying at the top level.

## Files to Change

- `src/trip_planner/core/__init__.py` — new, empty package marker
- `src/trip_planner/core/domain.py` — moved from `src/trip_planner/domain.py`, no content change
- `src/trip_planner/core/models.py` — moved from `src/trip_planner/models.py`; update its `from trip_planner.domain import InterestId` to `from trip_planner.core.domain import InterestId`
- `src/trip_planner/search/__init__.py` — new, empty package marker
- `src/trip_planner/search/serper_places.py` — moved from `src/trip_planner/serper_places.py`; update imports to `trip_planner.core.domain` / `trip_planner.core.models`
- `src/trip_planner/enrichment/__init__.py` — new, empty package marker
- `src/trip_planner/enrichment/venue_processing.py` — moved from `src/trip_planner/venue_processing.py`; update imports (`trip_planner.core.domain`, `trip_planner.core.models`, `trip_planner.enrichment.serper_lookup`, `trip_planner.search.serper_places`, `trip_planner.consolidation.standard_venues`, `trip_planner.enrichment.venue_cost`, `trip_planner.consolidation.venue_deduplication`, `trip_planner.enrichment.venue_description`, `trip_planner.enrichment.venue_details`, `trip_planner.enrichment.venue_distance`, `trip_planner.enrichment.venue_meal_tags`)
- `src/trip_planner/enrichment/serper_lookup.py` — moved; update `from trip_planner.venue_url_selection import rank_urls` to `trip_planner.enrichment.venue_url_selection`
- `src/trip_planner/enrichment/venue_url_selection.py` — moved from `src/trip_planner/venue_url_selection.py`; update `openai_client` import to `trip_planner.integrations.openai_client`
- `src/trip_planner/enrichment/venue_description.py` — moved; update imports to `trip_planner.core.domain`, `trip_planner.integrations.openai_client`
- `src/trip_planner/enrichment/venue_details.py` — moved; update `openai_client` import
- `src/trip_planner/enrichment/venue_meal_tags.py` — moved; update imports to `trip_planner.core.domain`, `trip_planner.integrations.openai_client`
- `src/trip_planner/enrichment/venue_cost.py` — moved; update imports to `trip_planner.core.domain`, `trip_planner.integrations.openai_client`
- `src/trip_planner/enrichment/venue_operating_hours.py` — moved; update `openai_client` import
- `src/trip_planner/enrichment/venue_distance.py` — moved from `src/trip_planner/venue_distance.py`; update `trip_planner.models` import to `trip_planner.core.models`
- `src/trip_planner/consolidation/__init__.py` — new, empty package marker
- `src/trip_planner/consolidation/venue_deduplication.py` — moved; update imports to `trip_planner.core.models`, `trip_planner.integrations.openai_client`
- `src/trip_planner/consolidation/venue_geo_clustering.py` — moved from `src/trip_planner/venue_geo_clustering.py`; update `trip_planner.models` import to `trip_planner.core.models`
- `src/trip_planner/consolidation/standard_venues.py` — moved; update imports to `trip_planner.core.models`, `trip_planner.enrichment.venue_cost`
- `src/trip_planner/consolidation/standard_meal_description.py` — moved; update `openai_client` import
- `src/trip_planner/scheduling/__init__.py` — new, empty package marker
- `src/trip_planner/scheduling/itinerary.py` — moved from `src/trip_planner/itinerary.py`; update imports to `trip_planner.core.domain`, `trip_planner.core.models`, `trip_planner.consolidation.standard_meal_description`, `trip_planner.consolidation.venue_geo_clustering`, `trip_planner.enrichment.venue_operating_hours`
- `src/trip_planner/integrations/__init__.py` — new, empty package marker
- `src/trip_planner/integrations/openai_client.py` — moved from `src/trip_planner/openai_client.py`, no content change
- `src/trip_planner/ui/__init__.py` — new, empty package marker
- `src/trip_planner/ui/ui.py` — moved from `src/trip_planner/ui.py`; update imports to `trip_planner.trip_planner` (unchanged path), `trip_planner.ui.validation`, `trip_planner.core.domain`
- `src/trip_planner/ui/assets.py` — moved from `src/trip_planner/assets.py`, no content change
- `src/trip_planner/ui/validation.py` — moved from `src/trip_planner/validation.py`; update `openai_client` import to `trip_planner.integrations.openai_client`
- `src/trip_planner/trip_planner.py` — stays at top level; update imports to `trip_planner.core.domain`, `trip_planner.scheduling.itinerary`, `trip_planner.core.models`, `trip_planner.search.serper_places`, `trip_planner.enrichment.venue_processing`
- `src/trip_planner/app.py` — stays at top level; update imports to `trip_planner.ui.assets`, `trip_planner.ui.ui`
- `src/trip_planner/__init__.py` — unchanged (already empty)
- `tests/search/test_serper_places.py` — moved from `tests/test_serper_places.py`; update imports
- `tests/enrichment/test_venue_processing.py` — moved; update imports (including `trip_planner.enrichment.venue_processing._executor`)
- `tests/enrichment/test_serper_lookup.py` — moved; update imports
- `tests/enrichment/test_venue_url_selection.py` — moved; update imports
- `tests/enrichment/test_venue_description.py` — moved; update imports
- `tests/enrichment/test_venue_details.py` — moved; update imports
- `tests/enrichment/test_venue_meal_tags.py` — moved; update imports
- `tests/enrichment/test_venue_cost.py` — moved; update imports
- `tests/enrichment/test_venue_operating_hours.py` — moved; update imports
- `tests/enrichment/test_venue_distance.py` — moved; update imports
- `tests/consolidation/test_venue_deduplication.py` — moved; update imports
- `tests/consolidation/test_venue_geo_clustering.py` — moved; update imports
- `tests/consolidation/test_standard_venues.py` — moved; update imports
- `tests/consolidation/test_standard_meal_description.py` — moved; update imports
- `tests/scheduling/test_itinerary.py` — moved; update imports
- `tests/integrations/test_openai_client.py` — moved; update imports
- `tests/ui/test_ui.py` — moved; update imports (including `trip_planner.trip_planner.STAGE_*` constants, unchanged path)
- `tests/ui/test_assets.py` — moved; update imports
- `tests/ui/test_validation.py` — moved; update imports
- `tests/test_trip_planner.py` — stays at top level; update imports
- `CLAUDE.md` — update the "Domain model", "Pipeline", and "Other entry points" subsections of Architecture to describe the new folder layout and each module's new path
- `README.md` — update the file paths referenced in its customization/pointers section (`openai_client.py`, `trip_planner.py`/`venue_processing.py`, `ui.py`) to their new locations

## Implementation Steps

1. Create the new subpackages under `src/trip_planner/`: `core/`, `search/`, `enrichment/`, `consolidation/`, `scheduling/`, `integrations/`, `ui/`, each with an empty `__init__.py`.
2. Move each source file into its target subfolder per the mapping in "Files to Change", using `git mv` so history is preserved.
3. Update every intra-package `from trip_planner.<module> import ...` statement across the moved files (and `trip_planner.py`/`app.py`, which stay put but import moved modules) to the new dotted paths.
4. Create the matching test subfolders under `tests/`: `search/`, `enrichment/`, `consolidation/`, `scheduling/`, `integrations/`, `ui/`, and move each test file into place with `git mv`.
5. Update every `from trip_planner.<module> import ...` statement in the moved test files to the new dotted paths.
6. Run `uv run pytest` and resolve any import errors or collection issues (e.g. add empty `__init__.py` files under the new `tests/` subfolders if pytest's rootdir-based test discovery needs them to disambiguate modules).
7. Run `uv run app` (or otherwise launch the Gradio UI) to confirm the entry point still resolves and the app starts without import errors.
8. Update `CLAUDE.md`'s Architecture section to describe the new folder-by-pipeline-stage layout and each module's new location.
9. Update the file paths referenced in `README.md` to match the new locations.
10. Re-run `uv run pytest` once more after the documentation pass to confirm nothing was missed.

## Testing

- `uv run pytest` must pass in full after the move, with every existing test case intact (no behavior or assertions changed) and only import paths updated.
- Manually launch the app (`uv run app`) and confirm the Gradio UI loads and the existing entry point path in `pyproject.toml` still resolves correctly.
- Spot-check that no leftover references to the old flat module paths remain (e.g. `grep -rn "from trip_planner\.\(domain\|models\|serper_places\|serper_lookup\|venue_\|standard_\|itinerary\|openai_client\|ui\|assets\|validation\) import"` across `src/` and `tests/` after the move should only match modules that legitimately still live at those paths, i.e. none — everything except `trip_planner` and `app` moved).

## Risks / Open Questions

- Hatchling's default src-layout package discovery is expected to auto-include the new subpackages since each has an `__init__.py`, but this should be verified by building/installing (`uv sync`) after the move in case `pyproject.toml` needs an explicit `[tool.hatch.build.targets.wheel]` packages list.
- Pytest's test discovery/import mode may require `__init__.py` files in the new `tests/` subfolders to avoid module-name collisions; this is called out as a fallback in Implementation Step 6 rather than assumed upfront.
- The `ui/ui.py` naming (a module named `ui` inside a package also named `ui`) is intentionally kept per the Assumptions section; flag to the user if this reads as confusing in practice.
