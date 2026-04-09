# Context Pad Repository Recovery Notes

This PR is intended to republish and retain the `context_pad/` package and related design docs in Git history.

## What to verify after merge

- `context_pad/` exists in the default branch.
- `context_pad/manifest/manifest.json` exists.
- Core docs (`CONTEXT_PAD_*.md`) exist in the repository root.

## Retention recommendations

- Protect the default branch from force-push.
- Require PR merges (no direct pushes) for structural deletes.
- Add CODEOWNERS approval for `context_pad/**` and `CONTEXT_PAD_*.md`.
- Mirror the repository to a backup remote.
