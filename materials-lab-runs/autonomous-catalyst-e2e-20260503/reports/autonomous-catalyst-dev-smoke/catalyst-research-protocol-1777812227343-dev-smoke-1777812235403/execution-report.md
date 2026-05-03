# Research Plan Execution: catalyst-research-protocol-1777812227343-dev-smoke-1777812235403

## Backend

- Backend: `dev-smoke`
- Confidence: `none`
- This backend validates execution plumbing only and does not create research property evidence.

## Summary

- Completed calculations: 10
- Skipped calculations: 0
- Allow blocked dev-smoke execution: `True`

## Completed Diagnostics

| Calculation | Material | Formula | Suppressed Properties |
| --- | --- | --- | --- |
| global-research-protocol-review |  |  | protocolReview |
| global-literature-evidence-ledger |  |  | literatureBaseline, knownControls, failureModes |
| global-database-candidate-search |  |  | candidatePool, databaseSummary |
| mp-675030-structure-preflight | mp-675030 | TiNiO3 | structurePath, cifPath, structureQuality |
| mp-675030-literature-benchmark | mp-675030 | TiNiO3 | literatureBaseline |
| mp-675030-database-provenance | mp-675030 | TiNiO3 | databaseSummary |
| mp-675030-phase-stability | mp-675030 | TiNiO3 | energyAboveHullEv, decompositionProducts |
| mp-675030-structure-validity | mp-675030 | TiNiO3 | structureQuality, oxidationStates, chargeBalance |
| mp-675030-synthesis-safety | mp-675030 | TiNiO3 | synthesisRoute, toxicityFlags, supplyRisk |
| mp-675030-surface-activity | mp-675030 | TiNiO3 | adsorptionEnergyEv, overpotentialV, selectivityScore |

## Warnings

- dev-smoke backend validates execution plumbing only; it does not generate property evidence or reranking updates.
