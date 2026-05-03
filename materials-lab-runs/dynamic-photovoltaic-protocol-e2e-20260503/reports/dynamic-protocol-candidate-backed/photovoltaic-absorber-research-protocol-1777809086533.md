# Dynamic Research Protocol: Photovoltaic absorber

## Objective

Design a lead-free moisture-stable photovoltaic absorber discovery campaign.

## Protocol Compiler

- Protocol version: `dynamic-research-protocol-v1`
- Topic inference: `keyword-derived`
- Matched keywords: photovoltaic, solar, absorber

## Autonomy Boundary

- Execution status: `planned-not-started`
- Requested autonomy mode: `high-autonomy-plan`
- Approval policy: `approval-required`
- Can execute without approval: `False`

## Candidate Generation

- Strategy: use live database candidates when available; otherwise use explicit development fixture smoke data only
- Initial candidate count: 3
- Database queries: Materials Project search for Design a lead-free moisture-stable photovoltaic absorber discovery campaign. | structure and stability query for Photovoltaic absorber
- Literature queries: Design a lead-free moisture-stable photovoltaic absorber discovery campaign. review | Design a lead-free moisture-stable photovoltaic absorber discovery campaign. benchmark materials | Photovoltaic absorber experimental validation

## Evidence Schema

| ID | Label | Evidence Types | Property Keys | Required |
| --- | --- | --- | --- | --- |
| literature-benchmark | Literature benchmark | literature | literatureBaseline | True |
| database-provenance | Database provenance | database | databaseSummary | True |
| phase-stability | Phase stability | database, dft | energyAboveHullEv, decompositionProducts | True |
| structure-validity | Structure and chemistry validity | database, workflow | structureQuality, oxidationStates, chargeBalance | True |
| synthesis-safety | Synthesis, toxicity, and handling risk | literature, safety, experiment | synthesisRoute, toxicityFlags, supplyRisk | True |
| optical-absorption | Optical absorption | dft, experiment | absorptionCoefficientCm1, directBandGapEv | True |
| defect-transport | Defect and transport risk | dft | defectToleranceScore, effectiveMassElectron, effectiveMassHole | True |
| environmental-health-safety | Environmental health and safety | safety, literature | ehsRisk, regulatoryFlags | True |
| reproducibility | Reproducibility package | workflow | workflowManifest, inputDecks, parsedOutputs | True |

## Selected Candidates

| Rank | Material | Formula | Evidence Tier | Source Level | Missing Properties | Planned Calculations |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | mp-21713 | K2In3CuSe6 | database-shortlist | database-summary | absorptionCoefficientCm1, directBandGapEv, effectiveMassElectron, effectiveMassHole, defectToleranceScore, literatureBaseline | mp-21713-structure-preflight, mp-21713-literature-benchmark, mp-21713-database-provenance, mp-21713-phase-stability, mp-21713-structure-validity, mp-21713-synthesis-safety, mp-21713-optical-absorption, mp-21713-defect-transport, mp-21713-environmental-health-safety, mp-21713-reproducibility |
| 2 | mp-1224609 | In2Ga(CuSe2)3 | database-shortlist | database-summary | absorptionCoefficientCm1, directBandGapEv, effectiveMassElectron, effectiveMassHole, defectToleranceScore, literatureBaseline | mp-1224609-structure-preflight |

## Protocol Queue

| ID | Material | Label | Backend | Method | Cost | Est. Hours | Writes |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| global-research-protocol-review | - | Research protocol and evidence schema review | agent-review | review compiled goal, candidate-generation strategy, evidence schema, claim policy, and stop criteria | metadata | 0.25 | protocolReview |
| global-literature-evidence-ledger | - | Literature evidence ledger | literature-connector | search, cite, and extract claims from literature queries | metadata | 1.0 | literatureBaseline, knownControls, failureModes |
| global-database-candidate-search | - | Database candidate generation | materials_search_mp | run database queries and build source-tagged candidate pool | metadata | 0.5 | candidatePool, databaseSummary |
| mp-21713-structure-preflight | mp-21713 | Structure fetch and normalization preflight | materials-lab | fetch_structure + structural sanity checks | metadata | 0.05 | structurePath, cifPath, structureQuality |
| mp-21713-literature-benchmark | mp-21713 | Literature benchmark | literature-connector | citation-backed literature extraction | metadata | 1.0 | literatureBaseline |
| mp-21713-database-provenance | mp-21713 | Database provenance | database-tool | database query and provenance capture | metadata | 0.5 | databaseSummary |
| mp-21713-phase-stability | mp-21713 | Phase stability | external-backend | DFT workflow with convergence checks and parsed properties | medium | 8.0 | energyAboveHullEv, decompositionProducts |
| mp-21713-structure-validity | mp-21713 | Structure and chemistry validity | external-backend | multi-source evidence collection and parser-backed validation | medium | 2.0 | structureQuality, oxidationStates, chargeBalance |
| mp-21713-synthesis-safety | mp-21713 | Synthesis, toxicity, and handling risk | experimental-system | experimental protocol or imported measurement with calibration metadata | expensive | 72.0 | synthesisRoute, toxicityFlags, supplyRisk |
| mp-21713-optical-absorption | mp-21713 | Optical absorption | external-backend | experimental protocol or imported measurement with calibration metadata | expensive | 72.0 | absorptionCoefficientCm1, directBandGapEv |
| mp-21713-defect-transport | mp-21713 | Defect and transport risk | external-backend | DFT workflow with convergence checks and parsed properties | medium | 8.0 | defectToleranceScore, effectiveMassElectron, effectiveMassHole |
| mp-21713-environmental-health-safety | mp-21713 | Environmental health and safety | literature-connector | multi-source evidence collection and parser-backed validation | metadata | 1.0 | ehsRisk, regulatoryFlags |
| mp-21713-reproducibility | mp-21713 | Reproducibility package | external-backend | multi-source evidence collection and parser-backed validation | medium | 2.0 | workflowManifest, inputDecks, parsedOutputs |
| mp-1224609-structure-preflight | mp-1224609 | Structure fetch and normalization preflight | materials-lab | fetch_structure + structural sanity checks | metadata | 0.05 | structurePath, cifPath, structureQuality |

## Approval Gates

| Gate | Required | Status | Blocks |
| --- | --- | --- | --- |
| gate-0-human-plan-review | True | pending | global-research-protocol-review, global-literature-evidence-ledger, global-database-candidate-search, mp-21713-structure-preflight, mp-21713-literature-benchmark, mp-21713-database-provenance, mp-21713-phase-stability, mp-21713-structure-validity, mp-21713-synthesis-safety, mp-21713-optical-absorption, mp-21713-defect-transport, mp-21713-environmental-health-safety, mp-21713-reproducibility, mp-1224609-structure-preflight |
| gate-1-budget-confirmation | True | pending | mp-21713-phase-stability, mp-21713-structure-validity, mp-21713-synthesis-safety, mp-21713-optical-absorption, mp-21713-defect-transport, mp-21713-reproducibility |
| gate-2-expensive-method-approval | True | pending | mp-21713-synthesis-safety, mp-21713-optical-absorption |
| gate-3-safety-and-experiment-review | True | pending | mp-21713-synthesis-safety, mp-21713-optical-absorption, mp-21713-environmental-health-safety |
| gate-4-evidence-ledger-acceptance | True | pending | update-shortlist, export-final-report |
| gate-5-claim-policy-review | True | pending | research-grade-claim |

## Claim Policy

- all required evidence requirements pass or have documented waivers
- live database provenance and literature ledger are attached
- property values come from parsed calculation/experimental/literature artifacts with confidence labels
- negative and contradictory evidence are included
- reproducibility package contains inputs, outputs, parser versions, and reranking trace

## Stop Criteria

- candidateGenerationPlan produces no new candidates after query expansion
- budget.maxCalculations or budget.maxWallTimeHours is exhausted
- all selected candidates fail at least one required evidence gate
- at least one candidate satisfies required evidenceSchema ids: literature-benchmark, database-provenance, phase-stability, structure-validity, synthesis-safety, optical-absorption, defect-transport, environmental-health-safety, reproducibility
- claimPolicy.researchGradeRequires is satisfied for a promoted candidate
- human reviewer or configured governance policy stops the dynamic loop

## Warnings

- Planned calculation wall-time estimate exceeds maxWallTimeHours; trim queue before execution.
- Expensive calculations are present but blocked until allowExpensiveCalculations and explicit approval are set.
- Safety or experimental evidence steps are present and require external review before execution.
- Selected candidates still have 12 missing research-grade property field(s).
- Dynamic protocol compiler output is a research plan, not independent scientific validation.
