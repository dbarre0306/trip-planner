# Reorganize Source Code Into Folders

branch: feature/reorganize-source-code-into-folders

## Summary

All application source modules currently live as a flat list of files directly inside the top-level source package, with no subfolders to indicate how modules relate to one another. As the codebase has grown, this flat layout makes it hard to see, at a glance, which modules belong together (e.g. domain types, the venue enrichment pipeline, external API integrations, and the UI). This feature reorganizes the source code into a small set of subfolders grouped by pipeline stage (e.g. domain/data types, venue enrichment, external service integrations, and the UI layer) so related modules are grouped together and the top level of the package only contains a handful of top-level items instead of dozens of individual files.

## Acceptance Criteria

- [ ] Source modules are grouped into subfolders based on pipeline stage (e.g. core domain/data types, the venue enrichment pipeline, external service integrations, and the UI layer) rather than sitting as a flat list of files at the top level of the source package.
- [ ] The grouping is discoverable and self-explanatory — a new contributor can tell what a module does by which folder it lives in.
- [ ] All existing functionality behaves exactly as before the reorganization; this is a structural change only, with no change in application behavior, UI, or pipeline output.
- [ ] All existing automated tests pass after the reorganization, updated as needed to reflect new module locations.
- [ ] The application still launches and runs successfully after the reorganization.
- [ ] Documentation that references the old file layout (e.g. CLAUDE.md's Architecture section) is updated to reflect the new folder structure.

## Scope

### In Scope

- Reorganizing existing source modules into subfolders by concern/purpose.
- Updating internal imports/references so the application continues to work after the move.
- Updating or relocating the corresponding test files to mirror the new structure.
- Updating project documentation (CLAUDE.md) that describes the current file layout.

### Out of Scope

- Changing any business logic, pipeline behavior, or UI behavior.
- Renaming or redesigning public-facing behavior, prompts, or the Gradio UI itself.
- Introducing new features, frameworks, or dependencies.
- Changing the project's build/packaging configuration beyond what's required to reflect the new source layout.

## Testing

- The full existing test suite must continue to pass after the reorganization, with test files relocated/updated to mirror the new source structure.
- No new test scenarios are required since behavior is unchanged; existing tests serve as the regression safety net for the move.
