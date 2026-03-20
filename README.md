# GHES Sync Tools

GitHub Actions workflows for synchronizing Actions and CodeQL bundles from GitHub.com to a GitHub Enterprise Server (GHES) instance.

## Purpose

Air-gapped or restricted GHES environments cannot reach GitHub.com at runtime. These workflows run on internet-connected runners to pull the latest tooling and push it into GHES so that Actions and CodeQL remain up to date.

## Workflows

### Actions Sync

| Workflow | Runner | Schedule |
|---|---|---|
| `lin-actions-sync.yml` | Linux | Weekly — Saturdays at 02:00 UTC |
| `win-actions-sync.yml` | Windows | Weekly — Saturdays at 02:00 UTC |

These workflows use the [actions/actions-sync](https://github.com/actions/actions-sync) tool to mirror a curated list of GitHub Actions repositories (defined in `repo-name-list.txt`) into GHES. Steps performed:

1. Download the latest `actions-sync` release.
2. Run `actions-sync sync` against the GHES instance, caching bundles locally.
3. Clean up temporary files.

### CodeQL Action Sync

| Workflow | Runner | Schedule |
|---|---|---|
| `lin-codeql-action-sync.yml` | Linux | Weekly — Sundays at 02:00 UTC |
| `win-codeql-action-sync.yml` | Windows | Weekly — Sundays at 02:00 UTC |

These workflows use the [github/codeql-action-sync-tool](https://github.com/github/codeql-action-sync-tool) to mirror the CodeQL Action and its analysis bundles into GHES. Steps performed:

1. Download the latest `codeql-action-sync` release.
2. Pull the CodeQL Action bundle and all release assets into a local cache.
3. Remove macOS and `.tar.gz` assets to reduce storage and transfer overhead (`.tar.zst` assets are kept).
4. Push the remaining assets to the GHES instance.

## Required Secrets and Variables

| Name | Type | Used By | Description |
|---|---|---|---|
| `ACTIONS_SYNC` | Secret | Actions Sync workflows | PAT with access to push Actions repos to GHES |
| `CODEQL_ACTION_SYNC_TOKEN` | Secret | CodeQL Sync workflows | PAT with access to push CodeQL assets to GHES |
| `GHES_URL` | Variable | Actions Sync workflows | Base URL of the GHES instance |

> The CodeQL Sync workflows have the GHES destination URL hard-coded in the workflow files.

## Supporting Files

- **`repo-name-list.txt`** — List of `org/repo` entries that the Actions Sync workflows will mirror to GHES.

## Manual Trigger

All workflows support `workflow_dispatch`, so they can be triggered on demand from the GitHub Actions UI in addition to their scheduled runs.
