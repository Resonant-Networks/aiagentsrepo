# AGENTS.md - 01 Project

This is the Antigravity workspace for the `01 Project`. When working here, follow these conventions.

## Project overview

The `01 Project` groups several infrastructure and operations subprojects. Sibling folders live alongside this workspace in the parent directory:

- NMS AI
- Onyx
- Openchamber
- Proxmox
- ZPE
- Zabbix
- strongswan

## Workspace rules

- Work only within the `01 Project` tree unless the user explicitly grants access elsewhere.
- Keep project config under `.agents/` in this workspace.
- Prefer declarative configuration (YAML/JSON/toml) over imperative scripts where the platform supports it.
- Verify changes with the project's own test/lint tooling before finishing a task.
- Do not commit secrets or credentials to the repository.

## Conventions

- Use the same naming and style conventions as the sibling project it targets.
- Document non-obvious infrastructure decisions in the affected project's own docs or logs.
- When the user references a sibling project, run `agy` scoped to that project's directory or pass `--add-dir` pointing at it.
