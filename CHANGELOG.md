# Changelog

## 0.10.1 - 2026-06-07

- Fixed implement persistence and authoring coherence checks to use the Core
  public browser contract when validating executable browser intent and network
  evidence.

## 0.10.0 - 2026-06-06

- Added Core public contract driven authoring for run requests, browser skills,
  credential references, report coverage interpretation, and agent guidance.
- Added fail-closed blockers for missing or malformed Core executable contract
  sections and legacy executable artifact schemas.
- Kept Core contract projections ephemeral per command; no Core contract
  snapshots are persisted into target `.proofsignal/` workspaces.
