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

- Strategy: discover candidates from Materials Project and literature before ranking
- Initial candidate count: 0
- Database queries: lead-free photovoltaic absorber candidates band gap 1.0-1.8 eV | stable chalcogenide oxide photovoltaic absorbers Materials Project
- Literature queries: lead-free moisture-stable photovoltaic absorbers review | thin-film solar absorber defect tolerance moisture stability

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
| - | - | - | - | - | Candidate generation pending | - |

## Protocol Queue

| ID | Material | Label | Backend | Method | Cost | Est. Hours | Writes |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| global-research-protocol-review | - | Research protocol and evidence schema review | agent-review | review compiled goal, candidate-generation strategy, evidence schema, claim policy, and stop criteria | metadata | 0.25 | protocolReview |
| global-literature-evidence-ledger | - | Literature evidence ledger | literature-connector | search, cite, and extract claims from literature queries | metadata | 1.0 | literatureBaseline, knownControls, failureModes |
| global-database-candidate-search | - | Database candidate generation | materials_search_mp | run database queries and build source-tagged candidate pool | metadata | 0.5 | candidatePool, databaseSummary |

## Approval Gates

| Gate | Required | Status | Blocks |
| --- | --- | --- | --- |
| gate-0-human-plan-review | True | pending | global-research-protocol-review, global-literature-evidence-ledger, global-database-candidate-search |
| gate-1-budget-confirmation | True | pending |  |
| gate-2-expensive-method-approval | False | pending |  |
| gate-3-safety-and-experiment-review | False | pending |  |
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

- No candidates were supplied; this protocol starts with candidate generation and evidence-schema compilation.
- Dynamic protocol compiler output is a research plan, not independent scientific validation.
