# Dynamic Research Protocol: Solid electrolyte / ion conductor

## Objective

Validate a live Materials Project proxy shortlist of lithium solid-state electrolyte candidates without overclaiming ionic conductivity.

## Protocol Compiler

- Protocol version: `dynamic-research-protocol-v1`
- Topic inference: `keyword-derived`
- Matched keywords: electrolyte

## Autonomy Boundary

- Execution status: `planned-not-started`
- Requested autonomy mode: `bounded`
- Approval policy: `plan-only`
- Can execute without approval: `False`

## Candidate Generation

- Strategy: Start broad, gather literature/database candidates, then narrow by evidence schema and diversity controls.
- Initial candidate count: 4
- Database queries: Materials Project search for Validate a live Materials Project proxy shortlist of lithium solid-state electrolyte candidates without overclaiming ionic conductivity. | structure and stability query for Solid electrolyte / ion conductor
- Literature queries: Validate a live Materials Project proxy shortlist of lithium solid-state electrolyte candidates without overclaiming ionic conductivity. review | Validate a live Materials Project proxy shortlist of lithium solid-state electrolyte candidates without overclaiming ionic conductivity. benchmark materials | Solid electrolyte / ion conductor experimental validation

## Literature Evidence Pipeline

- Pipeline version: `literature-evidence-pipeline-v1`
- Parsers: JSON/JSONL/CSV evidence, text/markdown citation extraction, optional PDF text extraction
- Maps to evidence: literature-benchmark, synthesis-safety, li-transport, electrochemical-window, interface-stability

## Method Registry

- Registry version: `domain-method-registry-v1`
- Topic: `solid-electrolyte`

| Requirement | Methods |
| --- | --- |
| literature-benchmark | citation search, PDF/text/table extraction, contradictory evidence capture |
| database-provenance | define domain method, attach parser-backed evidence, review uncertainty/conflicts |
| phase-stability | database convex-hull provenance, DFT relaxation and decomposition analysis |
| structure-validity | structure parser preflight, oxidation-state/charge-balance sanity checks |
| synthesis-safety | define domain method, attach parser-backed evidence, review uncertainty/conflicts |
| electronic-insulation | define domain method, attach parser-backed evidence, review uncertainty/conflicts |
| li-transport | define domain method, attach parser-backed evidence, review uncertainty/conflicts |
| electrochemical-window | grand-potential phase stability, interface reaction energy |
| interface-stability | define domain method, attach parser-backed evidence, review uncertainty/conflicts |
| reproducibility | input/output bundle, parser version manifest, claim audit certificate |

## Autonomous Discovery

- Enabled: `False`
- Status: `skipped-existing-candidates`
- Source mode: `None`
- Queries: 0 / 0
- Ranked candidates: 4
- Candidate pool: -
- Evidence ledger: -

## Evidence Schema

| ID | Label | Evidence Types | Property Keys | Required |
| --- | --- | --- | --- | --- |
| literature-benchmark | Literature benchmark | literature | literatureBaseline | True |
| database-provenance | Database provenance | database | databaseSummary | True |
| phase-stability | Phase stability | database, dft | energyAboveHullEv, decompositionProducts | True |
| structure-validity | Structure and chemistry validity | database, workflow | structureQuality, oxidationStates, chargeBalance | True |
| synthesis-safety | Synthesis, toxicity, and handling risk | literature, safety, experiment | synthesisRoute, toxicityFlags, supplyRisk | True |
| electronic-insulation | Electronic insulation | database, dft | bandGapEv | True |
| li-transport | Li-ion transport | md, dft, literature, experiment | ionicConductivityScm, migrationBarrierEv | True |
| electrochemical-window | Electrochemical window | dft, literature, experiment | electrochemicalWindowV | True |
| interface-stability | Electrode interface stability | dft, literature, experiment | interfaceStability, interfaceReactionEnergyEv | True |
| reproducibility | Reproducibility package | workflow | workflowManifest, inputDecks, parsedOutputs | True |

## Selected Candidates

| Rank | Material | Formula | Evidence Tier | Source Level | Missing Properties | Planned Calculations |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | mp-556886 | Li4Al3Ge3ClO12 | watchlist | proxy-only | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | mp-556886-structure-preflight, mp-556886-literature-benchmark, mp-556886-database-provenance, mp-556886-phase-stability, mp-556886-structure-validity, mp-556886-synthesis-safety, mp-556886-li-transport, mp-556886-electrochemical-window, mp-556886-interface-stability, mp-556886-reproducibility |
| 2 | mp-554203 | Li4Ga3Si3ClO12 | watchlist | proxy-only | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | mp-554203-structure-preflight, mp-554203-literature-benchmark, mp-554203-database-provenance |
| 3 | mp-567652 | Cs2LiYCl6 | watchlist | proxy-only | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | - |
| 4 | mp-11175 | LiZnPS4 | watchlist | proxy-only | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | - |

## Protocol Queue

| ID | Material | Label | Backend | Method | Cost | Est. Hours | Writes |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| global-research-protocol-review | - | Research protocol and evidence schema review | agent-review | review compiled goal, candidate-generation strategy, evidence schema, claim policy, and stop criteria | metadata | 0.25 | protocolReview |
| global-literature-evidence-ledger | - | Literature evidence ledger | literature-connector | search, cite, extract PDF/text/table claims, and normalize citation provenance | metadata | 1.0 | literatureBaseline, knownControls, failureModes, citationProvenance |
| global-database-candidate-search | - | Database candidate generation | materials_search_mp | run database queries and build source-tagged candidate pool | metadata | 0.5 | candidatePool, databaseSummary |
| mp-556886-structure-preflight | mp-556886 | Structure fetch and normalization preflight | materials-lab | fetch_structure + structural sanity checks | metadata | 0.05 | structurePath, cifPath, structureQuality |
| mp-556886-literature-benchmark | mp-556886 | Literature benchmark | literature-connector | citation-backed literature extraction | metadata | 1.0 | literatureBaseline |
| mp-556886-database-provenance | mp-556886 | Database provenance | database-tool | database query and provenance capture | metadata | 0.5 | databaseSummary |
| mp-556886-phase-stability | mp-556886 | Phase stability | external-backend | DFT workflow with convergence checks and parsed properties | medium | 8.0 | energyAboveHullEv, decompositionProducts |
| mp-556886-structure-validity | mp-556886 | Structure and chemistry validity | external-backend | multi-source evidence collection and parser-backed validation | medium | 2.0 | structureQuality, oxidationStates, chargeBalance |
| mp-556886-synthesis-safety | mp-556886 | Synthesis, toxicity, and handling risk | experimental-system | experimental protocol or imported measurement with calibration metadata | expensive | 72.0 | synthesisRoute, toxicityFlags, supplyRisk |
| mp-556886-li-transport | mp-556886 | Li-ion transport | external-backend | experimental protocol or imported measurement with calibration metadata | expensive | 72.0 | ionicConductivityScm, migrationBarrierEv |
| mp-556886-electrochemical-window | mp-556886 | Electrochemical window | external-backend | experimental protocol or imported measurement with calibration metadata | expensive | 72.0 | electrochemicalWindowV |
| mp-556886-interface-stability | mp-556886 | Electrode interface stability | external-backend | experimental protocol or imported measurement with calibration metadata | expensive | 72.0 | interfaceStability, interfaceReactionEnergyEv |
| mp-556886-reproducibility | mp-556886 | Reproducibility package | external-backend | multi-source evidence collection and parser-backed validation | medium | 2.0 | workflowManifest, inputDecks, parsedOutputs |
| mp-554203-structure-preflight | mp-554203 | Structure fetch and normalization preflight | materials-lab | fetch_structure + structural sanity checks | metadata | 0.05 | structurePath, cifPath, structureQuality |
| mp-554203-literature-benchmark | mp-554203 | Literature benchmark | literature-connector | citation-backed literature extraction | metadata | 1.0 | literatureBaseline |
| mp-554203-database-provenance | mp-554203 | Database provenance | database-tool | database query and provenance capture | metadata | 0.5 | databaseSummary |

## Approval Gates

| Gate | Required | Status | Blocks |
| --- | --- | --- | --- |
| gate-0-human-plan-review | False | pending | global-research-protocol-review, global-literature-evidence-ledger, global-database-candidate-search, mp-556886-structure-preflight, mp-556886-literature-benchmark, mp-556886-database-provenance, mp-556886-phase-stability, mp-556886-structure-validity, mp-556886-synthesis-safety, mp-556886-li-transport, mp-556886-electrochemical-window, mp-556886-interface-stability, mp-556886-reproducibility, mp-554203-structure-preflight, mp-554203-literature-benchmark, mp-554203-database-provenance |
| gate-1-budget-confirmation | True | pending | mp-556886-phase-stability, mp-556886-structure-validity, mp-556886-synthesis-safety, mp-556886-li-transport, mp-556886-electrochemical-window, mp-556886-interface-stability, mp-556886-reproducibility |
| gate-2-expensive-method-approval | True | pending | mp-556886-synthesis-safety, mp-556886-li-transport, mp-556886-electrochemical-window, mp-556886-interface-stability |
| gate-3-safety-and-experiment-review | True | pending | mp-556886-synthesis-safety, mp-556886-li-transport, mp-556886-electrochemical-window, mp-556886-interface-stability |
| gate-4-evidence-ledger-acceptance | True | pending | update-shortlist, export-final-report |
| gate-5-claim-policy-review | True | pending | research-grade-claim |

## Claim Policy

- all required evidence requirements pass or have documented waivers
- live database provenance and literature ledger are attached
- property values come from parsed calculation/experimental/literature artifacts with confidence labels
- negative and contradictory evidence are included
- uncertainty/conflict engine reports confidence above threshold with no material numeric conflict
- reproducibility package contains inputs, outputs, parser versions, and reranking trace

## Stop Criteria

- candidateGenerationPlan produces no new candidates after query expansion
- budget.maxCalculations or budget.maxWallTimeHours is exhausted
- all selected candidates fail at least one required evidence gate
- at least one candidate satisfies required evidenceSchema ids: literature-benchmark, database-provenance, phase-stability, structure-validity, synthesis-safety, electronic-insulation, li-transport, electrochemical-window, interface-stability, reproducibility
- claimPolicy.researchGradeRequires is satisfied for a promoted candidate
- human reviewer or configured governance policy stops the dynamic loop

## Warnings

- Approval policy is not approval-required; the generated plan still marks compute execution as blocked until explicit approval.
- Planned calculation wall-time estimate exceeds maxWallTimeHours; trim queue before execution.
- Expensive calculations are present but blocked until allowExpensiveCalculations and explicit approval are set.
- Selected candidates still have 16 missing research-grade property field(s).
- Dynamic protocol compiler output is a research plan, not independent scientific validation.
