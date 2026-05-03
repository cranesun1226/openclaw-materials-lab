# Dynamic Research Protocol: Catalyst / surface material

## Objective

Discover lead-free noble-metal-free oxygen evolution catalyst candidates for alkaline water splitting.

## Protocol Compiler

- Protocol version: `dynamic-research-protocol-v1`
- Topic inference: `keyword-derived`
- Matched keywords: catalyst

## Autonomy Boundary

- Execution status: `planned-not-started`
- Requested autonomy mode: `high-autonomy-plan`
- Approval policy: `approval-required`
- Can execute without approval: `False`

## Candidate Generation

- Strategy: search live database candidates from transition-metal oxide/sulfide catalyst families before ranking
- Initial candidate count: 3
- Database queries: Materials Project search for Discover lead-free noble-metal-free oxygen evolution catalyst candidates for alkaline water splitting. | structure and stability query for Catalyst / surface material
- Literature queries: Discover lead-free noble-metal-free oxygen evolution catalyst candidates for alkaline water splitting. review | Discover lead-free noble-metal-free oxygen evolution catalyst candidates for alkaline water splitting. benchmark materials | Catalyst / surface material experimental validation

## Autonomous Discovery

- Enabled: `True`
- Status: `completed`
- Source mode: `materials-project-live`
- Queries: 6 / 6
- Ranked candidates: 3
- Candidate pool: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/candidate-pool.jsonl
- Evidence ledger: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/evidence-ledger.jsonl

## Evidence Schema

| ID | Label | Evidence Types | Property Keys | Required |
| --- | --- | --- | --- | --- |
| literature-benchmark | Literature benchmark | literature | literatureBaseline | True |
| database-provenance | Database provenance | database | databaseSummary | True |
| phase-stability | Phase stability | database, dft | energyAboveHullEv, decompositionProducts | True |
| structure-validity | Structure and chemistry validity | database, workflow | structureQuality, oxidationStates, chargeBalance | True |
| synthesis-safety | Synthesis, toxicity, and handling risk | literature, safety, experiment | synthesisRoute, toxicityFlags, supplyRisk | True |
| surface-activity | Surface activity and selectivity | dft, experiment | adsorptionEnergyEv, overpotentialV, selectivityScore | True |
| operando-stability | Operando stability | dft, experiment | surfaceStability, dissolutionRisk | True |
| environmental-health-safety | Environmental health and safety | safety, literature | ehsRisk, regulatoryFlags | True |
| reproducibility | Reproducibility package | workflow | workflowManifest, inputDecks, parsedOutputs | True |

## Selected Candidates

| Rank | Material | Formula | Evidence Tier | Source Level | Missing Properties | Planned Calculations |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | mp-675030 | TiNiO3 | proxy-shortlist | summary-only | domain-specific-property-model | mp-675030-structure-preflight, mp-675030-literature-benchmark, mp-675030-database-provenance, mp-675030-phase-stability, mp-675030-structure-validity, mp-675030-synthesis-safety, mp-675030-surface-activity, mp-675030-operando-stability, mp-675030-environmental-health-safety, mp-675030-reproducibility |
| 2 | mp-690546 | TiNiO3 | proxy-shortlist | summary-only | domain-specific-property-model | mp-690546-structure-preflight, mp-690546-literature-benchmark, mp-690546-database-provenance |
| 3 | mp-19009 | NiO | proxy-shortlist | summary-only | domain-specific-property-model | - |

## Protocol Queue

| ID | Material | Label | Backend | Method | Cost | Est. Hours | Writes |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| global-research-protocol-review | - | Research protocol and evidence schema review | agent-review | review compiled goal, candidate-generation strategy, evidence schema, claim policy, and stop criteria | metadata | 0.25 | protocolReview |
| global-literature-evidence-ledger | - | Literature evidence ledger | literature-connector | search, cite, and extract claims from literature queries | metadata | 1.0 | literatureBaseline, knownControls, failureModes |
| global-database-candidate-search | - | Database candidate generation | materials_search_mp | run database queries and build source-tagged candidate pool | metadata | 0.5 | candidatePool, databaseSummary |
| mp-675030-structure-preflight | mp-675030 | Structure fetch and normalization preflight | materials-lab | fetch_structure + structural sanity checks | metadata | 0.05 | structurePath, cifPath, structureQuality |
| mp-675030-literature-benchmark | mp-675030 | Literature benchmark | literature-connector | citation-backed literature extraction | metadata | 1.0 | literatureBaseline |
| mp-675030-database-provenance | mp-675030 | Database provenance | database-tool | database query and provenance capture | metadata | 0.5 | databaseSummary |
| mp-675030-phase-stability | mp-675030 | Phase stability | external-backend | DFT workflow with convergence checks and parsed properties | medium | 8.0 | energyAboveHullEv, decompositionProducts |
| mp-675030-structure-validity | mp-675030 | Structure and chemistry validity | external-backend | multi-source evidence collection and parser-backed validation | medium | 2.0 | structureQuality, oxidationStates, chargeBalance |
| mp-675030-synthesis-safety | mp-675030 | Synthesis, toxicity, and handling risk | experimental-system | experimental protocol or imported measurement with calibration metadata | expensive | 72.0 | synthesisRoute, toxicityFlags, supplyRisk |
| mp-675030-surface-activity | mp-675030 | Surface activity and selectivity | external-backend | experimental protocol or imported measurement with calibration metadata | expensive | 72.0 | adsorptionEnergyEv, overpotentialV, selectivityScore |
| mp-675030-operando-stability | mp-675030 | Operando stability | external-backend | experimental protocol or imported measurement with calibration metadata | expensive | 72.0 | surfaceStability, dissolutionRisk |
| mp-675030-environmental-health-safety | mp-675030 | Environmental health and safety | literature-connector | multi-source evidence collection and parser-backed validation | metadata | 1.0 | ehsRisk, regulatoryFlags |
| mp-675030-reproducibility | mp-675030 | Reproducibility package | external-backend | multi-source evidence collection and parser-backed validation | medium | 2.0 | workflowManifest, inputDecks, parsedOutputs |
| mp-690546-structure-preflight | mp-690546 | Structure fetch and normalization preflight | materials-lab | fetch_structure + structural sanity checks | metadata | 0.05 | structurePath, cifPath, structureQuality |
| mp-690546-literature-benchmark | mp-690546 | Literature benchmark | literature-connector | citation-backed literature extraction | metadata | 1.0 | literatureBaseline |
| mp-690546-database-provenance | mp-690546 | Database provenance | database-tool | database query and provenance capture | metadata | 0.5 | databaseSummary |

## Approval Gates

| Gate | Required | Status | Blocks |
| --- | --- | --- | --- |
| gate-0-human-plan-review | True | pending | global-research-protocol-review, global-literature-evidence-ledger, global-database-candidate-search, mp-675030-structure-preflight, mp-675030-literature-benchmark, mp-675030-database-provenance, mp-675030-phase-stability, mp-675030-structure-validity, mp-675030-synthesis-safety, mp-675030-surface-activity, mp-675030-operando-stability, mp-675030-environmental-health-safety, mp-675030-reproducibility, mp-690546-structure-preflight, mp-690546-literature-benchmark, mp-690546-database-provenance |
| gate-1-budget-confirmation | True | pending | mp-675030-phase-stability, mp-675030-structure-validity, mp-675030-synthesis-safety, mp-675030-surface-activity, mp-675030-operando-stability, mp-675030-reproducibility |
| gate-2-expensive-method-approval | True | pending | mp-675030-synthesis-safety, mp-675030-surface-activity, mp-675030-operando-stability |
| gate-3-safety-and-experiment-review | True | pending | mp-675030-synthesis-safety, mp-675030-surface-activity, mp-675030-operando-stability, mp-675030-environmental-health-safety |
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
- at least one candidate satisfies required evidenceSchema ids: literature-benchmark, database-provenance, phase-stability, structure-validity, synthesis-safety, surface-activity, operando-stability, environmental-health-safety, reproducibility
- claimPolicy.researchGradeRequires is satisfied for a promoted candidate
- human reviewer or configured governance policy stops the dynamic loop

## Warnings

- Planned calculation wall-time estimate exceeds maxWallTimeHours; trim queue before execution.
- Expensive calculations are present but blocked until allowExpensiveCalculations and explicit approval are set.
- Safety or experimental evidence steps are present and require external review before execution.
- Selected candidates still have 3 missing research-grade property field(s).
- Dynamic protocol compiler output is a research plan, not independent scientific validation.
