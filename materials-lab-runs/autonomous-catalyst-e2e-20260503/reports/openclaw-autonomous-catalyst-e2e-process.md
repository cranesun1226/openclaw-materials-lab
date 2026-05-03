# OpenClaw Autonomous Catalyst E2E

## Verdict

- Status: `passed`
- Topic: Discover lead-free noble-metal-free oxygen evolution catalyst candidates for alkaline water splitting.
- Completed at: 2026-05-03T12:44:10.229Z

OpenClaw Materials Lab autonomously compiled a catalyst research protocol from a topic, discovered live Materials Project candidates, wrote evidence artifacts, and prepared backend inputs without making research-grade claims.

This is a workflow validation, not a research-grade catalyst discovery claim.

## Discovery

- Status: `completed`
- Source mode: `materials-project-live`
- Queries: 6 / 6
- Ranked candidates: 3
- Candidate pool: materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/candidate-pool.jsonl
- Evidence ledger: materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/evidence-ledger.jsonl

## Selected Candidates

| Rank | Material | Formula | Source | Score | Evidence Tier |
| ---: | --- | --- | --- | ---: | --- |
| 1 | mp-675030 | TiNiO3 | materials-project | 0.875032 | proxy-shortlist |
| 2 | mp-690546 | TiNiO3 | materials-project | 0.868638 | proxy-shortlist |
| 3 | mp-19009 | NiO | materials-project | 0.847952 | proxy-shortlist |

## Protocol

- Evidence schema: literature-benchmark, database-provenance, phase-stability, structure-validity, synthesis-safety, surface-activity, operando-stability, environmental-health-safety, reproducibility
- Queue steps: 16
- Approval gates: 6
- Research-grade claim allowed: `false`

## Execution

- Structure fetched: materials-lab-runs/autonomous-catalyst-e2e-20260503/structures/mp-675030/mp-675030.json
- dev-smoke completed: 10
- dev-smoke property updates: 0
- Quantum ESPRESSO prepared: 7
- Quantum ESPRESSO submitted: 0

## Checks

| Result | Check | Detail |
| --- | --- | --- |
| pass | bridge-ping | Materials Lab worker 0.1.0 is ready. |
| pass | protocol-version | dynamic-research-protocol-v1 |
| pass | topic-inference | {"id":"catalyst","label":"Catalyst / surface material","inference":"keyword-derived","matchedKeywords":["catalyst"],"alternateTopics":[]} |
| pass | autonomous-discovery-enabled | {"enabled":true,"status":"completed","sourceMode":"materials-project-live","queryCount":6,"successfulQueryCount":6,"candidateCount":50,"rankedCandidateCount":3,"queryLogPath":"/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/query-log.json","candidatePoolPath":"/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/candidate-pool.jsonl","evidenceLedgerPath":"/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/evidence-ledger.jsonl","summaryPath":"/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/summary.json"} |
| pass | autonomous-discovery-completed | {"enabled":true,"status":"completed","sourceMode":"materials-project-live","queryCount":6,"successfulQueryCount":6,"candidateCount":50,"rankedCandidateCount":3,"queryLogPath":"/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/query-log.json","candidatePoolPath":"/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/candidate-pool.jsonl","evidenceLedgerPath":"/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/evidence-ledger.jsonl","summaryPath":"/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/summary.json"} |
| pass | live-source-mode | materials-project-live |
| pass | candidate-pool-nonempty | selected=3 |
| pass | surface-activity-schema | literature-benchmark, database-provenance, phase-stability, structure-validity, synthesis-safety, surface-activity, operando-stability, environmental-health-safety, reproducibility |
| pass | operando-stability-schema | literature-benchmark, database-provenance, phase-stability, structure-validity, synthesis-safety, surface-activity, operando-stability, environmental-health-safety, reproducibility |
| pass | claim-locked | {"currentLevel":"candidate-hypothesis","researchGradeClaimAllowed":false,"blockedBy":["evidence-ledger-review","parsed-property-evidence","claim-policy-review"],"reason":"The autonomous design engine can propose and rank candidates, but research-grade claims require closed evidenceSchema entries."} |
| pass | candidate-pool-artifact | /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/candidate-pool.jsonl |
| pass | evidence-ledger-artifact | /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/evidence-ledger.jsonl |
| pass | excluded-elements-filtered | mp-675030, mp-690546, mp-19009 |
| pass | live-structure-fetch | Fetched structure for mp-675030 and wrote 2 artifact(s). |
| pass | dev-smoke-completed | Executed dev-smoke backend: 10 completed, 0 prepared, 0 submitted, 0 skipped. |
| pass | dev-smoke-no-property-updates | propertyUpdates=0 |
| pass | qe-prepared | Prepared quantum-espresso backend: 0 completed, 7 prepared, 0 submitted, 9 skipped. |
| pass | qe-not-submitted | submittedCalculations=0 |
| pass | qe-scf-input | /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-phase-stability/pw.scf.in |
| pass | candidate-pool-live | /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/candidate-pool.jsonl |
| pass | ledger-blocks-research-grade | /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/evidence-ledger.jsonl |

## Artifacts

| Exists | Path | Bytes |
| --- | --- | ---: |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/catalyst-research-protocol-1777812227343.json | 44909 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/catalyst-research-protocol-1777812227343.md | 10039 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/query-log.json | 4018 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/candidate-pool.jsonl | 10990 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/evidence-ledger.jsonl | 5854 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-plan/autonomous-discovery/summary.json | 1122 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/structures/mp-675030/mp-675030.json | 15476 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/structures/mp-675030/mp-675030.cif | 2723 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-dev-smoke/catalyst-research-protocol-1777812227343-dev-smoke-1777812235403/execution-manifest.json | 13010 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-dev-smoke/catalyst-research-protocol-1777812227343-dev-smoke-1777812235403/execution-report.md | 1481 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-dev-smoke/catalyst-research-protocol-1777812227343-dev-smoke-1777812235403/global-research-protocol-review.json | 1158 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-dev-smoke/catalyst-research-protocol-1777812227343-dev-smoke-1777812235403/global-literature-evidence-ledger.json | 1149 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-dev-smoke/catalyst-research-protocol-1777812227343-dev-smoke-1777812235403/global-database-candidate-search.json | 1127 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-dev-smoke/catalyst-research-protocol-1777812227343-dev-smoke-1777812235403/mp-675030-structure-preflight.json | 1144 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-dev-smoke/catalyst-research-protocol-1777812227343-dev-smoke-1777812235403/mp-675030-literature-benchmark.json | 1080 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-dev-smoke/catalyst-research-protocol-1777812227343-dev-smoke-1777812235403/mp-675030-database-provenance.json | 1073 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-dev-smoke/catalyst-research-protocol-1777812227343-dev-smoke-1777812235403/mp-675030-phase-stability.json | 1109 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-dev-smoke/catalyst-research-protocol-1777812227343-dev-smoke-1777812235403/mp-675030-structure-validity.json | 1154 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-dev-smoke/catalyst-research-protocol-1777812227343-dev-smoke-1777812235403/mp-675030-synthesis-safety.json | 1161 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-dev-smoke/catalyst-research-protocol-1777812227343-dev-smoke-1777812235403/mp-675030-surface-activity.json | 1166 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/execution-manifest.json | 27088 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/execution-report.md | 1166 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-structure-preflight/step-manifest.json | 2830 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-phase-stability/step-manifest.json | 3517 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-structure-validity/step-manifest.json | 3587 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-surface-activity/step-manifest.json | 3568 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-operando-stability/step-manifest.json | 3555 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-reproducibility/step-manifest.json | 3534 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-690546-structure-preflight/step-manifest.json | 2830 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-structure-preflight/structure.json | 15476 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-structure-preflight/structure.cif | 2723 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-structure-preflight/POSCAR | 2972 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-structure-preflight/preflight-note.md | 308 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-phase-stability/structure.json | 15476 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-phase-stability/structure.cif | 2723 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-phase-stability/POSCAR | 2972 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-phase-stability/pw.scf.in | 2242 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-phase-stability/PSEUDOPOTENTIALS.required | 20 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-phase-stability/run.sh | 70 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-structure-validity/structure.json | 15476 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-structure-validity/structure.cif | 2723 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-structure-validity/POSCAR | 2972 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-structure-validity/pw.scf.in | 2242 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-structure-validity/PSEUDOPOTENTIALS.required | 20 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-structure-validity/run.sh | 70 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-surface-activity/structure.json | 15476 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-surface-activity/structure.cif | 2723 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-surface-activity/POSCAR | 2972 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-surface-activity/pw.scf.in | 2242 |
| yes | materials-lab-runs/autonomous-catalyst-e2e-20260503/reports/autonomous-catalyst-qe-prepare/catalyst-research-protocol-1777812227343-quantum-espresso-1777812238244/mp-675030-surface-activity/PSEUDOPOTENTIALS.required | 20 |
