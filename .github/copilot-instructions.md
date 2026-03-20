# Copilot Instructions

## Repository Overview

This repo contains GitHub Actions workflow definitions (not application code) for syncing Actions and CodeQL bundles from GitHub.com into an air-gapped GitHub Enterprise Server (GHES) instance. There are no build, test, or lint steps.

## Architecture

Every sync tool has a **Linux + Windows pair** of workflow files at the repo root:

- `lin-actions-sync.yml` / `win-actions-sync.yml` — mirror Actions repos via [actions/actions-sync](https://github.com/actions/actions-sync)
- `lin-codeql-action-sync.yml` / `win-codeql-action-sync.yml` — mirror CodeQL bundles via [github/codeql-action-sync-tool](https://github.com/github/codeql-action-sync-tool)

Linux workflows use Bash; Windows workflows use `shell: pwsh` (PowerShell Core). Both variants must stay functionally equivalent — when editing one, update its counterpart.

## Conventions

- **Workflow files live at the repo root**, not under `.github/workflows/`. They are reference templates meant to be copied into consuming repositories.
- **Linux uses `curl`/`jq`/`tar`; Windows uses `Invoke-RestMethod`/`Invoke-WebRequest`/`Expand-Archive` or `tar`.** Keep platform-idiomatic tooling in each variant.
- **Runner labels**: Linux workflows use `Ent_Linux_runners` (or `linux`); Windows workflows use `Ent_Windows_runners` (or `windows-latest`). These are org-specific self-hosted runner labels.
- **Asset pruning**: CodeQL sync workflows deliberately remove macOS (`*osx*`) and `.tar.gz` assets, keeping only `.tar.zst`, to minimize GHES storage. Preserve this filtering when modifying those workflows.
- **Secrets/variables**: `ACTIONS_SYNC` and `GHES_URL` are used by Actions Sync workflows. `CODEQL_ACTION_SYNC_TOKEN` is used by CodeQL workflows. The GHES destination URL in CodeQL workflows is hard-coded rather than using a variable.
