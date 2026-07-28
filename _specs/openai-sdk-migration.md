# OpenAI SDK Migration

branch: claude/feature/openai-sdk-migration

## Summary

CrewAI has been judged the wrong solution for this application's needs. This feature replaces CrewAI as the orchestration/agent framework throughout the project with direct use of the OpenAI API/SDK. Every place that currently relies on CrewAI constructs (agents, tasks, crews, YAML-based agent/task configuration, and the CLI entry points built around them) is re-implemented using OpenAI API calls instead, while preserving the application's existing external behavior (e.g. venue processing still produces the same kind of results it does today).

## User Story

As a maintainer of this application, I want the AI-driven parts of the app to call the OpenAI API/SDK directly instead of going through CrewAI, so that the project has a simpler, more directly controllable dependency that better fits how this application actually uses AI.

## Acceptance Criteria

- [ ] No part of the application depends on the CrewAI package or its constructs (agents, tasks, crews, YAML agent/task configuration) at runtime.
- [ ] Every capability that previously ran through a CrewAI agent/task/crew has an equivalent implementation built on the OpenAI API/SDK, producing behaviorally equivalent results.
- [ ] The application's existing entry points (however they are exposed today) continue to work, now backed by the OpenAI SDK instead of CrewAI.
- [ ] Configuration previously expressed as CrewAI YAML (agent roles/goals/backstories, task descriptions/expected outputs) is replaced with an equivalent way of configuring prompts/behavior for the OpenAI-based implementation.
- [ ] Project dependency and configuration files no longer declare CrewAI as a dependency or reference CrewAI-specific project settings.
- [ ] Existing automated tests are updated to reflect the new OpenAI-based implementation and continue to pass without invoking the real OpenAI API.

## Scope

### In Scope

- Removing CrewAI as a dependency and removing all CrewAI-specific code, configuration, and project settings.
- Reimplementing, using the OpenAI API/SDK, any behavior that previously ran through a CrewAI agent, task, or crew.
- Updating any project configuration (dependencies, entry points, tool-specific settings) that currently assumes a CrewAI-based project.
- Updating documentation and developer-facing guidance that describes how to work with the AI/agent portion of this codebase, so it reflects the OpenAI SDK approach instead of CrewAI.
- Updating existing automated tests so they exercise the new OpenAI-based implementation instead of CrewAI.

### Out of Scope

- Changing the application's non-AI business logic (e.g. venue lookup/search behavior, data models) beyond what's required to swap the underlying AI framework.
- Introducing new AI-driven features or capabilities beyond what already exists today.
- Choosing or evaluating alternative agent frameworks other than the OpenAI API/SDK.
- Changes to how the application is deployed or hosted, beyond what's strictly necessitated by removing CrewAI.

## UI / UX Notes

Not applicable — this is a backend/framework migration with no direct user-facing interface changes.

## Testing

- Existing automated tests covering AI-driven behavior should be updated to mock/stub the OpenAI SDK boundary instead of CrewAI, so no real API calls are made during test runs.
- Tests should confirm that the behaviorally equivalent OpenAI-based implementation produces the same kind of output the CrewAI-based version did for each capability being replaced.
- The full existing test suite should continue to pass after the migration.

## Open Questions

- Should the OpenAI SDK be called directly (e.g. via a single client/completions call per capability), or should some lightweight in-house structure be introduced to keep prompts, inputs, and outputs organized as more AI-driven capabilities are added later? directly
- Which OpenAI model(s) should be used, and should model choice be configurable (e.g. via environment variable) the way it partially is today? Only use one model defined in `.env`
- Are there any CrewAI-specific features currently relied upon (e.g. structured/pydantic outputs, multi-step task chaining) that need a specific equivalent approach when reimplemented directly against the OpenAI SDK? no
- Does this migration need to preserve any CrewAI-specific CLI commands (train/replay/test-style workflows), or can those be dropped entirely if they have no direct OpenAI SDK equivalent? drop if necessary
