# Live OpenClaw Dynamic Photovoltaic Protocol E2E

## Verdict

- Status: `passed`
- Candidate source mode: `materials-project-live`
- Topic: Design a lead-free moisture-stable photovoltaic absorber discovery campaign.
- Completed at: 2026-05-03T11:51:49.934Z

OpenClaw Materials Lab compiled and exercised a live-data dynamic research protocol. No research-grade discovery claim was made.

This run is an end-to-end software and workflow validation. It does not claim a new research-grade photovoltaic absorber discovery.

## OpenClaw Path

- Materials Lab configured: `true`
- Materials Project API key configured: `true`
- Python path: `/Users/haksunlee/.openclaw/materials-lab/.venv/bin/python`

## Live Search

| Query | Status | Candidates | Offline data |
| --- | --- | ---: | --- |
| silicon absorber baseline | ok | 1 | false |
| chalcopyrite selenide absorber family | ok | 2 | false |
| kesterite sulfide absorber family | ok | 0 | false |

## Protocol Compiler

- Protocol-only selected candidates: 0
- Candidate-backed selected candidates: 2
- Evidence schema: literature-benchmark, database-provenance, phase-stability, structure-validity, synthesis-safety, optical-absorption, defect-transport, environmental-health-safety, reproducibility
- Approval gates: 6

## Execution

- dev-smoke completed calculations: 8
- dev-smoke property updates: 0
- Quantum ESPRESSO prepared calculations: 7
- Quantum ESPRESSO submitted calculations: 0

## Checks

| Result | Check | Detail |
| --- | --- | --- |
| pass | bridge-ping | Materials Lab worker 0.1.0 is ready. |
| pass | live-search-silicon absorber baseline | candidateCount=1 |
| pass | live-search-chalcopyrite selenide absorber family | candidateCount=2 |
| pass | live-search-kesterite sulfide absorber family | candidateCount=0 |
| pass | candidate-pool | candidateCount=3; sourceMode=materials-project-live |
| pass | live-structure-fetch | Fetched structure for mp-149 and wrote 2 artifact(s). |
| pass | protocol-compiler-version | Compiled dynamic research protocol with 3 approval-gated step(s) for 0 selected candidate(s). |
| pass | protocol-without-candidates | selectedCandidates=0 |
| pass | photovoltaic-evidence-schema | literature-benchmark, database-provenance, phase-stability, structure-validity, synthesis-safety, optical-absorption, defect-transport, environmental-health-safety, reproducibility |
| pass | candidate-backed-plan | Compiled dynamic research protocol with 14 approval-gated step(s) for 2 selected candidate(s). |
| pass | claim-policy-present | researchGradeRequires is present |
| pass | approval-gates-present | approvalGates=6 |
| pass | dev-smoke-completed | Executed dev-smoke backend: 8 completed, 0 prepared, 0 submitted, 0 skipped. |
| pass | dev-smoke-no-property-claims | propertyUpdates=0 |
| pass | qe-inputs-prepared | Prepared quantum-espresso backend: 0 completed, 7 prepared, 0 submitted, 7 skipped. |
| pass | qe-no-submission | submittedCalculations=0 |
| pass | qe-scf-input-contains-atomic-species | /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-phase-stability/pw.scf.in |

## Artifacts

| Exists | Path | Bytes |
| --- | --- | ---: |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/structures/mp-149/mp-149.json | 1285 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/structures/mp-149/mp-149.cif | 746 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-no-candidates/photovoltaic-absorber-research-protocol-1777809082886.json | 24519 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-no-candidates/photovoltaic-absorber-research-protocol-1777809082886.md | 4913 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-candidate-backed/photovoltaic-absorber-research-protocol-1777809086533.json | 39699 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-candidate-backed/photovoltaic-absorber-research-protocol-1777809086533.md | 8958 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-dev-smoke-execution/photovoltaic-absorber-research-protocol-1777809086533-dev-smoke-1777809090152/execution-manifest.json | 10711 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-dev-smoke-execution/photovoltaic-absorber-research-protocol-1777809086533-dev-smoke-1777809090152/execution-report.md | 1300 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-dev-smoke-execution/photovoltaic-absorber-research-protocol-1777809086533-dev-smoke-1777809090152/global-research-protocol-review.json | 1188 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-dev-smoke-execution/photovoltaic-absorber-research-protocol-1777809086533-dev-smoke-1777809090152/global-literature-evidence-ledger.json | 1179 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-dev-smoke-execution/photovoltaic-absorber-research-protocol-1777809086533-dev-smoke-1777809090152/global-database-candidate-search.json | 1157 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-dev-smoke-execution/photovoltaic-absorber-research-protocol-1777809086533-dev-smoke-1777809090152/mp-21713-structure-preflight.json | 1175 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-dev-smoke-execution/photovoltaic-absorber-research-protocol-1777809086533-dev-smoke-1777809090152/mp-21713-literature-benchmark.json | 1111 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-dev-smoke-execution/photovoltaic-absorber-research-protocol-1777809086533-dev-smoke-1777809090152/mp-21713-database-provenance.json | 1104 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-dev-smoke-execution/photovoltaic-absorber-research-protocol-1777809086533-dev-smoke-1777809090152/mp-21713-phase-stability.json | 1140 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-dev-smoke-execution/photovoltaic-absorber-research-protocol-1777809086533-dev-smoke-1777809090152/mp-21713-structure-validity.json | 1185 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/execution-manifest.json | 28024 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/execution-report.md | 1156 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-structure-preflight/step-manifest.json | 2984 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-phase-stability/step-manifest.json | 3728 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-structure-validity/step-manifest.json | 3798 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-optical-absorption/step-manifest.json | 3774 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-defect-transport/step-manifest.json | 3779 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-reproducibility/step-manifest.json | 3745 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-1224609-structure-preflight/step-manifest.json | 3007 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-structure-preflight/structure.json | 18297 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-structure-preflight/structure.cif | 3194 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-structure-preflight/POSCAR | 3551 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-structure-preflight/preflight-note.md | 310 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-phase-stability/structure.json | 18297 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-phase-stability/structure.cif | 3194 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-phase-stability/POSCAR | 3551 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-phase-stability/pw.scf.in | 2634 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-phase-stability/PSEUDOPOTENTIALS.required | 27 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-phase-stability/run.sh | 70 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-structure-validity/structure.json | 18297 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-structure-validity/structure.cif | 3194 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-structure-validity/POSCAR | 3551 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-structure-validity/pw.scf.in | 2634 |
| yes | materials-lab-runs/dynamic-photovoltaic-protocol-e2e-20260503/reports/dynamic-protocol-qe-prepare/photovoltaic-absorber-research-protocol-1777809086533-quantum-espresso-1777809093906/mp-21713-structure-validity/PSEUDOPOTENTIALS.required | 27 |
