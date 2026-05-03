# Live Materials Project Solid-State Electrolyte Candidate Screening

## Research Goal

Use OpenClaw Materials Lab with a live Materials Project API key to shortlist stable lithium-containing inorganic candidates for solid-state battery electrolyte exploration.

## Evaluation Criteria

- Live Materials Project source only; offline fallback disabled.
- Energy above hull <= 0.1 eV for preliminary stability screening.
- Band gap between 2.0 and 8.5 eV, ranked toward a 5.0 eV target as an electronic-insulation proxy.
- Density alignment toward 3.0 g/cm3 as a lightweight proxy for inorganic solid electrolyte families.
- Top candidates must have retrievable structures for downstream analysis.
- This demo does not compute Li-ion conductivity, migration barriers, or electrochemical stability windows.

## Ranked Candidates

### 1. mp-759280 (LiZr2(PO4)3)

- Score: 0.938947
- Source: materials-project
- stability score 0.960
- band-gap alignment 0.886
- density alignment 0.993

### 2. mp-10499 (LiZr2(PO4)3)

- Score: 0.936746
- Source: materials-project
- stability score 1.000
- band-gap alignment 0.851
- density alignment 0.927

### 3. mp-773068 (LiZr2(PO4)3)

- Score: 0.923921
- Source: materials-project
- stability score 0.944
- band-gap alignment 0.862
- density alignment 0.999

### 4. mp-681439 (LiZr2(PO4)3)

- Score: 0.904112
- Source: materials-project
- stability score 0.920
- band-gap alignment 0.846
- density alignment 0.985

### 5. mp-541661 (LiZr2(PO4)3)

- Score: 0.884761
- Source: materials-project
- stability score 0.911
- band-gap alignment 0.828
- density alignment 0.930

### 6. mp-1223743 (Li2Zr4As3(PO8)3)

- Score: 0.88263
- Source: materials-project
- stability score 0.940
- band-gap alignment 0.797
- density alignment 0.890

### 7. mp-773074 (LiZr2(PO4)3)

- Score: 0.878595
- Source: materials-project
- stability score 0.843
- band-gap alignment 0.878
- density alignment 0.998

### 8. mp-1222872 (Li2Zr4As3(PO8)3)

- Score: 0.844328
- Source: materials-project
- stability score 0.898
- band-gap alignment 0.743
- density alignment 0.901

### 9. mp-942733 (Li7La3Zr2O12)

- Score: 0.824046
- Source: materials-project
- stability score 0.966
- band-gap alignment 0.834
- density alignment 0.329

### 10. mp-11175 (LiZnPS4)

- Score: 0.816047
- Source: materials-project
- stability score 1.000
- band-gap alignment 0.546
- density alignment 0.832

## Notes

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/notes/2026-05-03T06-39-02-325Z-live-materials-project-solid-state-electrolyte-screening-process.md

## Artifacts

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/plots/solid-electrolyte-ranking/candidate-ranking.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-759280/mp-759280.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-759280/mp-759280.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-759280/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-10499/mp-10499.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-10499/mp-10499.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-10499/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-773068/mp-773068.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-773068/mp-773068.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-20260503/structures/mp-773068/structure-metrics.png

## Limitations

- Ranking depends on the chosen criteria and available data.
- Offline/mock mode should not be treated as equivalent to live database validation.

