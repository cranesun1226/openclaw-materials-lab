# Research Plan Execution: photovoltaic-absorber-research-protocol-1777808979714-dev-smoke-1777809001160

## Backend

- Backend: `dev-smoke`
- Confidence: `none`
- This backend validates execution plumbing only and does not create research property evidence.

## Summary

- Completed calculations: 8
- Skipped calculations: 0
- Allow blocked dev-smoke execution: `True`

## Completed Diagnostics

| Calculation | Material | Formula | Suppressed Properties |
| --- | --- | --- | --- |
| global-research-protocol-review |  |  | protocolReview |
| global-literature-evidence-ledger |  |  | literatureBaseline, knownControls, failureModes |
| global-database-candidate-search |  |  | candidatePool, databaseSummary |
| fixture-si-structure-preflight | fixture-si | Si | structurePath, cifPath, structureQuality |
| fixture-si-literature-benchmark | fixture-si | Si | literatureBaseline |
| fixture-si-database-provenance | fixture-si | Si | databaseSummary |
| fixture-si-phase-stability | fixture-si | Si | energyAboveHullEv, decompositionProducts |
| fixture-si-structure-validity | fixture-si | Si | structureQuality, oxidationStates, chargeBalance |

## Warnings

- dev-smoke backend validates execution plumbing only; it does not generate property evidence or reranking updates.
