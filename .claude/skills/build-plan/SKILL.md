---
name: build-plan
description: Build a feature plan file
argument-hint: Path or slug of a spec file under _specs/
allowed-tools: Read, Write, Glob
disable-model-invocation: true
---

You are helping to turn an existing feature spec into an implementation plan. Always adhere to any rules or requirements set out in any CLAUDE.md files when responding.

Specification File: $ARGUMENTS

## High level behavior

Your job is to turn the spec file referenced above into a detailed markdown implementation plan, saved under the `_plans/` directory using the same base name as the spec file. Do NOT implement the plan.

## Step 1. Resolve the spec file

`$ARGUMENTS` may be a full path (e.g. `_specs/card-component.md`) or just a slug (e.g. `card-component`). If it's not already a path ending in `.md`, use Glob to find a matching file under `_specs/`. If no spec file can be found, or more than one plausibly matches, stop and ask the user to clarify instead of guessing.

## Step 2. Read the spec

Read the resolved spec file in full. If it is missing required sections (e.g. no Acceptance Criteria, no Scope) such that a plan can't be produced responsibly, stop and tell the user what's missing instead of guessing at intent.

## Step 3. Draft the plan content

Create a markdown plan document using the exact structure defined in the plan template file here: @_plans/template.md. If the template file is missing or its structure is unclear, stop and tell the user instead of guessing at a structure.

The plan should:

- Reference the spec file it was built from.
- Cover every Acceptance Criterion and respect the spec's In Scope / Out of Scope split.
- List concrete files to change or create, and ordered implementation steps.
- Not include actual code — describe changes, don't write them.

## Step 4. Save the plan

Save the plan to `_plans/<feature-slug>.md`, using the same base name as the spec file (e.g. `_specs/card-component.md` → `_plans/card-component.md`).

## Step 5. Final output to the user

After the file is saved, respond with a short summary in this exact format:

Spec file: _specs/<feature-slug>.md
Plan file: _plans/<feature-slug>.md

Do not repeat the full plan in the chat output unless the user explicitly asks to see it.

Step 5 is the last step of this skill. This skill produces one deliverable — the saved plan file — and nothing else. It is not a request awaiting approval to implement. Once the summary above is printed, stop:

- Do not ask, in any wording, whether to proceed, implement, or execute the plan (e.g. "Would you like me to proceed?", "Should I start implementing this?", "Ready to execute — proceed?"). This applies in every mode, including Plan Mode.
- Do not call the `ExitPlanMode` tool from this skill, even if Plan Mode is active. Writing and saving the plan file is an explicit exception to Plan Mode's edit restrictions for this skill — it is the action this skill exists to perform, not a plan to be approved.
- Always automatically save the plan file regardless of mode.
- Do not take any further action or ask any follow-up question.
