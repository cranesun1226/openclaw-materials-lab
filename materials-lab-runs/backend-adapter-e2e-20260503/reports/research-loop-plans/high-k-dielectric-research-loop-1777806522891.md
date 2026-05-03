# Research Loop Plan: high-k-dielectric

## Objective

Validate external backend adapter preparation for high-k dielectric HfO2.

## Autonomy Boundary

- Execution status: `planned-not-started`
- Approval policy: `approval-required`
- Can execute without approval: `False`

## Selected Candidates

| Rank | Material | Formula | Evidence Tier | Source Level | Missing Properties | Planned Calculations |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | mp-mock-hfo2 | HfO2 | proxy-shortlist | proxy-only | dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv | mp-mock-hfo2-structure-preflight, mp-mock-hfo2-dfpt-dielectric-tensor, mp-mock-hfo2-band-alignment |

## Calculation Queue

| ID | Material | Label | Method | Cost | Est. Hours | Writes |
| --- | --- | --- | --- | --- | ---: | --- |
| mp-mock-hfo2-structure-preflight | mp-mock-hfo2 | Structure fetch and normalization preflight | fetch_structure + structural sanity checks | metadata | 0.05 | structurePath, cifPath, structureQuality |
| mp-mock-hfo2-dfpt-dielectric-tensor | mp-mock-hfo2 | DFPT dielectric tensor | DFPT electronic + ionic dielectric calculation | expensive | 12.0 | dielectricTotal, dielectricElectronic |
| mp-mock-hfo2-band-alignment | mp-mock-hfo2 | Band offsets | absolute band alignment against target channel | medium | 6.0 | bandOffsetElectronEv, bandOffsetHoleEv |

## Approval Gates

| Gate | Required | Status | Blocks |
| --- | --- | --- | --- |
| gate-0-human-plan-review | True | pending | mp-mock-hfo2-structure-preflight, mp-mock-hfo2-dfpt-dielectric-tensor, mp-mock-hfo2-band-alignment |
| gate-1-budget-confirmation | True | pending | mp-mock-hfo2-dfpt-dielectric-tensor, mp-mock-hfo2-band-alignment |
| gate-2-expensive-method-approval | True | pending | mp-mock-hfo2-dfpt-dielectric-tensor |
| gate-3-rerank-acceptance | True | pending | update-shortlist, export-final-report |

## Stop Criteria

- at least one candidate reaches domainEvidence.tier == research-shortlist
- domainCoverage.sourceLevelCounts.property-backed is nonzero
- budget.maxCalculations or budget.maxWallTimeHours is exhausted
- all candidates retain fail gates after required property calculations
- human reviewer stops the high-k-dielectric loop

## Warnings

- Expensive calculations are present but blocked until allowExpensiveCalculations and human approval are explicit.
- Selected candidates still have 4 missing research-grade property field(s).
