# Research Loop Plan: high-k-dielectric

## Objective

Execute the first local-surrogate backend pass for high-k candidates and produce property updates for reranking.

## Autonomy Boundary

- Execution status: `planned-not-started`
- Approval policy: `approval-required`
- Can execute without approval: `False`

## Selected Candidates

| Rank | Material | Formula | Evidence Tier | Source Level | Missing Properties | Planned Calculations |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | mp-1143 | Al2O3 | proxy-shortlist | proxy-only | dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv, phononStability | mp-1143-structure-preflight, mp-1143-dfpt-dielectric-tensor, mp-1143-band-alignment, mp-1143-interface-reaction, mp-1143-phonon-stability |
| 2 | mp-2652 | Y2O3 | proxy-shortlist | proxy-only | dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv, phononStability | mp-2652-structure-preflight, mp-2652-dfpt-dielectric-tensor, mp-2652-band-alignment, mp-2652-interface-reaction, mp-2652-phonon-stability |
| 3 | mp-733790 | SiO2 | watchlist | proxy-only | dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv, phononStability | mp-733790-structure-preflight, mp-733790-dfpt-dielectric-tensor |

## Calculation Queue

| ID | Material | Label | Method | Cost | Est. Hours | Writes |
| --- | --- | --- | --- | --- | ---: | --- |
| mp-1143-structure-preflight | mp-1143 | Structure fetch and normalization preflight | fetch_structure + structural sanity checks | metadata | 0.05 | structurePath, cifPath, structureQuality |
| mp-1143-dfpt-dielectric-tensor | mp-1143 | DFPT dielectric tensor | DFPT electronic + ionic dielectric calculation | expensive | 12.0 | dielectricTotal, dielectricElectronic |
| mp-1143-band-alignment | mp-1143 | Band offsets | absolute band alignment against target channel | medium | 6.0 | bandOffsetElectronEv, bandOffsetHoleEv |
| mp-1143-interface-reaction | mp-1143 | Interface reaction energy | interface thermodynamics against target channel | medium | 6.0 | interfaceReactionEnergyEv |
| mp-1143-phonon-stability | mp-1143 | Phonon stability | phonon or imaginary-mode screen | expensive | 18.0 | phononStability |
| mp-2652-structure-preflight | mp-2652 | Structure fetch and normalization preflight | fetch_structure + structural sanity checks | metadata | 0.05 | structurePath, cifPath, structureQuality |
| mp-2652-dfpt-dielectric-tensor | mp-2652 | DFPT dielectric tensor | DFPT electronic + ionic dielectric calculation | expensive | 12.0 | dielectricTotal, dielectricElectronic |
| mp-2652-band-alignment | mp-2652 | Band offsets | absolute band alignment against target channel | medium | 6.0 | bandOffsetElectronEv, bandOffsetHoleEv |
| mp-2652-interface-reaction | mp-2652 | Interface reaction energy | interface thermodynamics against target channel | medium | 6.0 | interfaceReactionEnergyEv |
| mp-2652-phonon-stability | mp-2652 | Phonon stability | phonon or imaginary-mode screen | expensive | 18.0 | phononStability |
| mp-733790-structure-preflight | mp-733790 | Structure fetch and normalization preflight | fetch_structure + structural sanity checks | metadata | 0.05 | structurePath, cifPath, structureQuality |
| mp-733790-dfpt-dielectric-tensor | mp-733790 | DFPT dielectric tensor | DFPT electronic + ionic dielectric calculation | expensive | 12.0 | dielectricTotal, dielectricElectronic |

## Approval Gates

| Gate | Required | Status | Blocks |
| --- | --- | --- | --- |
| gate-0-human-plan-review | True | pending | mp-1143-structure-preflight, mp-1143-dfpt-dielectric-tensor, mp-1143-band-alignment, mp-1143-interface-reaction, mp-1143-phonon-stability, mp-2652-structure-preflight, mp-2652-dfpt-dielectric-tensor, mp-2652-band-alignment, mp-2652-interface-reaction, mp-2652-phonon-stability, mp-733790-structure-preflight, mp-733790-dfpt-dielectric-tensor |
| gate-1-budget-confirmation | True | pending | mp-1143-dfpt-dielectric-tensor, mp-1143-band-alignment, mp-1143-interface-reaction, mp-1143-phonon-stability, mp-2652-dfpt-dielectric-tensor, mp-2652-band-alignment, mp-2652-interface-reaction, mp-2652-phonon-stability, mp-733790-dfpt-dielectric-tensor |
| gate-2-expensive-method-approval | True | pending | mp-1143-dfpt-dielectric-tensor, mp-1143-phonon-stability, mp-2652-dfpt-dielectric-tensor, mp-2652-phonon-stability, mp-733790-dfpt-dielectric-tensor |
| gate-3-rerank-acceptance | True | pending | update-shortlist, export-final-report |

## Stop Criteria

- at least one candidate reaches domainEvidence.tier == research-shortlist
- domainCoverage.sourceLevelCounts.property-backed is nonzero
- budget.maxCalculations or budget.maxWallTimeHours is exhausted
- all candidates retain fail gates after required property calculations
- human reviewer stops the high-k-dielectric loop

## Warnings

- Planned calculation wall-time estimate exceeds maxWallTimeHours; trim queue before execution.
- Expensive calculations are present but blocked until allowExpensiveCalculations and human approval are explicit.
- Selected candidates still have 18 missing research-grade property field(s).
