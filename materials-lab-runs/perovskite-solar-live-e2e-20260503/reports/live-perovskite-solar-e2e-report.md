# Live Materials Project Perovskite Solar Candidate Screening

## Research Goal

Use OpenClaw Materials Lab with a live Materials Project API key to identify stable oxide perovskite-family candidates relevant to solar-material exploration.

## Evaluation Criteria

- Live Materials Project source only; offline fallback disabled.
- Energy above hull <= 0.05 eV for stability screening.
- Band gap between 1.0 and 4.2 eV, ranked toward a 2.8 eV target for this oxide-perovskite demo.
- Density alignment toward 5.0 g/cm3 as a lightweight proxy for compact inorganic oxide structures.
- Top candidates must have retrievable structures for downstream analysis.

## Ranked Candidates

### 1. mp-4514 (NaNbO3)

- Score: 0.942015
- Source: materials-project
- stability score 1.000
- band-gap alignment 0.895
- density alignment 0.895

### 2. mp-27790 (BaTi5O11)

- Score: 0.939723
- Source: materials-project
- stability score 0.961
- band-gap alignment 0.937
- density alignment 0.883

### 3. mp-504457 (BaTi6O13)

- Score: 0.933651
- Source: materials-project
- stability score 0.934
- band-gap alignment 0.943
- density alignment 0.909

### 4. mp-1403610 (CaTi2O5)

- Score: 0.932342
- Source: materials-project
- stability score 0.985
- band-gap alignment 0.961
- density alignment 0.697

### 5. mp-5020 (BaTiO3)

- Score: 0.931305
- Source: materials-project
- stability score 1.000
- band-gap alignment 0.896
- density alignment 0.820

### 6. mp-1218603 (Sr3Ti(GaO2)10)

- Score: 0.923009
- Source: materials-project
- stability score 0.900
- band-gap alignment 0.930
- density alignment 0.972

### 7. mp-5477 (Na5NbO5)

- Score: 0.920442
- Source: materials-project
- stability score 1.000
- band-gap alignment 0.942
- density alignment 0.624

### 8. mp-5777 (BaTiO3)

- Score: 0.900414
- Source: materials-project
- stability score 1.000
- band-gap alignment 0.819
- density alignment 0.819

## Notes

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/notes/2026-05-03T06-20-15-134Z-live-materials-project-perovskite-solar-screening-process.md

## Artifacts

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/plots/live-candidate-ranking/candidate-ranking.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-4514/mp-4514.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-4514/mp-4514.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-4514/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-27790/mp-27790.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-27790/mp-27790.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-27790/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-504457/mp-504457.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-504457/mp-504457.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-504457/structure-metrics.png

## Limitations

- Ranking depends on the chosen criteria and available data.
- Offline/mock mode should not be treated as equivalent to live database validation.

