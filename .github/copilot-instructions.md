# Copilot Cloud Agent Instructions — STU-Wiki

This repository is a **spec-kit** workspace. Its purpose is to drive structured,
specification-first software development using a set of Claude-powered skills and
shell scripts. There is no application source code in the repository yet; all
content is tooling, templates, and (future) feature specifications.

---

## Repository Layout

```
.specify/               # Spec-kit core — DO NOT edit manually
  memory/
    constitution.md     # Project constitution (currently a blank template)
  templates/            # Canonical templates: spec, plan, tasks, checklist, …
  integrations/         # Integration manifests (Claude, speckit)
  scripts/bash/         # Shell helpers (common.sh, create-new-feature.sh, …)

.claude/
  skills/               # Claude slash-command skills (speckit-*)
    speckit-analyze/
    speckit-checklist/
    speckit-clarify/
    speckit-constitution/
    speckit-implement/
    speckit-plan/
    speckit-specify/
    speckit-tasks/
    speckit-taskstoissues/

specs/                  # Created at runtime — one subdirectory per feature
  <NNN>-<feature-name>/ # e.g. 001-user-auth/
    spec.md             # Feature specification (output of speckit-specify)
    plan.md             # Implementation plan  (output of speckit-plan)
    tasks.md            # Task list            (output of speckit-tasks)
    research.md         # Phase-0 research
    data-model.md       # Data-model design
    quickstart.md       # How to run the feature
    contracts/          # API / service contracts
    checklists/         # Quality checklists
```

> **Note**: The `specs/` directory does not exist yet; it is created the first
> time a feature is specified.

---

## Speckit Workflow

Work through features in this order, one skill per step:

| Step | Skill | What it does |
|------|-------|--------------|
| 1 | `speckit-specify` | Turns a plain-English description into `spec.md` |
| 2 | `speckit-clarify` | Asks up to 5 targeted questions and encodes answers into the spec |
| 3 | `speckit-plan` | Researches the tech landscape and writes `plan.md` (+ `research.md`, `data-model.md`, `quickstart.md`, `contracts/`) |
| 4 | `speckit-tasks` | Generates a dependency-ordered `tasks.md` |
| 5 | `speckit-implement` | Executes every task in `tasks.md` sequentially |
| 6 | `speckit-analyze` | Cross-checks `spec.md`, `plan.md`, and `tasks.md` for consistency |
| 7 | `speckit-checklist` | Generates a custom quality checklist on demand |
| 8 | `speckit-taskstoissues` | Converts `tasks.md` entries into GitHub Issues |

Additional maintenance skill:

| Skill | What it does |
|-------|--------------|
| `speckit-constitution` | Creates or updates `.specify/memory/constitution.md` |

---

## Invoking Skills

Skills are invoked via the `skill` tool (or as slash commands in chat). Always
pass a descriptive argument to the skills that accept one:

```text
speckit-specify   "Add user authentication with OAuth2"
speckit-clarify   (no argument needed — reads the active spec)
speckit-plan      (no argument needed — reads the active spec)
speckit-tasks     (no argument needed — reads plan + spec)
speckit-implement (no argument needed — reads tasks.md)
```

The active feature directory is resolved in this priority order:

1. `SPECIFY_FEATURE_DIRECTORY` environment variable
2. `.specify/feature.json` → `feature_directory` key
3. Current git branch name prefix (e.g. `001` in `001-user-auth`)

---

## Branch & Directory Naming Conventions

Feature branches and spec directories share the same prefix format:

- **Sequential**: `NNN-short-name` — e.g. `003-analytics-dashboard`
- **Timestamp**: `YYYYMMDD-HHMMSS-short-name` — e.g. `20260501-182000-user-auth`

The spec directory lives at `specs/<prefix>-<short-name>/`. Branch name and spec
directory name are **independent** (they often match but don't have to).

---

## Key Files to Read First

When starting a task, always read these files for context:

1. `.specify/memory/constitution.md` — project principles (if filled in)
2. `specs/<feature>/spec.md` — what the feature must do
3. `specs/<feature>/plan.md` — how it will be built
4. `specs/<feature>/tasks.md` — ordered task list with `[P]` (parallel) markers

---

## Important Conventions

- **No application code exists yet.** Do not look for `src/`, `tests/`, or a
  build system — they don't exist until a feature spec drives their creation.
- **Spec files are technology-agnostic.** `spec.md` must not mention frameworks,
  languages, or databases. Those details belong in `plan.md`.
- **Constitution is the highest authority.** Once `.specify/memory/constitution.md`
  is filled in, all plans and implementations must comply with it.
- **`[P]` in tasks.md** means the task can run in parallel with other `[P]` tasks
  (different files, no dependencies).
- **Do not manually edit files under `.specify/templates/` or `.specify/scripts/`**
  unless fixing a bug — these are owned by the speckit tooling.
- **The `.specify/` directory is the spec-kit project marker.** The shell scripts
  in `.specify/scripts/bash/common.sh` walk up the directory tree to find it;
  always keep it at the repository root.

---

## No Build / Lint / Test Commands

This repository contains no application code and therefore has **no build,
lint, or test commands** to run. When a feature is implemented and adds code,
the `plan.md` for that feature will document the appropriate commands under its
**Technical Context** section and `quickstart.md`.

---

## Errors & Workarounds

| Situation | Workaround |
|-----------|------------|
| `specs/` directory missing | It is created automatically by `speckit-specify` on first use. |
| `.specify/feature.json` not found | Set `SPECIFY_FEATURE_DIRECTORY` env var or ensure you are on a correctly named feature branch. |
| Multiple spec dirs match a branch prefix | Each prefix must map to exactly one `specs/` directory. Rename or remove duplicates. |
| `jq` not available | Scripts fall back to `python3` JSON parsing, then to a single-line `grep` heuristic. Install `jq` for best results. |
| Constitution is blank | Run `speckit-constitution` to create the project constitution before planning significant features. |
