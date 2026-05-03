# Live OpenClaw Materials Lab E2E Process

Generated: 2026-05-03T06:20:18.601Z

## Question

Which stable oxide perovskite-family candidates from Materials Project are worth shortlisting for perovskite solar-material exploration?

## Process

- Used the real OpenClaw `materials-lab` configuration and Python worker.
- Read the Materials Project API key from `~/.openclaw/openclaw.json` without printing it.
- Disabled offline fallback in every live MP query.
- Queried Sr-Ti-O, Ba-Ti-O, Ca-Ti-O, and Na-Nb-O families.
- Ranked candidates with stability, band-gap alignment, and density alignment.
- Fetched and analyzed structures for the top ranked candidates.
- Exported the final markdown report and machine-readable JSON summary.

## Outputs

- Summary JSON: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/reports/live-perovskite-solar-e2e-summary.json
- Final report: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/reports/live-perovskite-solar-e2e-report.md
- Process note: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/notes/2026-05-03T06-20-15-134Z-live-materials-project-perovskite-solar-screening-process.md
- Ranking plot/artifacts: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/plots/live-candidate-ranking/candidate-ranking.png, /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-4514/mp-4514.json, /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-4514/mp-4514.cif, /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-4514/structure-metrics.png, /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-27790/mp-27790.json, /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-27790/mp-27790.cif, /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-27790/structure-metrics.png, /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-504457/mp-504457.json, /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-504457/mp-504457.cif, /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-live-e2e-20260503/structures/mp-504457/structure-metrics.png

## Top Candidates

- 1. mp-4514 (NaNbO3) score=0.942015, bandGap=2.5048, eHull=0
- 2. mp-27790 (BaTi5O11) score=0.939723, bandGap=2.6235, eHull=0.0077932558455890005
- 3. mp-504457 (BaTi6O13) score=0.933651, bandGap=2.6401, eHull=0.013269258593750001
- 4. mp-1403610 (CaTi2O5) score=0.932342, bandGap=2.9078, eHull=0.003020262656249
- 5. mp-5020 (BaTiO3) score=0.931305, bandGap=2.5086999999999993, eHull=0.00004098999996848818
- 6. mp-1218603 (Sr3Ti(GaO2)10) score=0.923009, bandGap=2.6054, eHull=0.020009235183824
- 7. mp-5477 (Na5NbO5) score=0.920442, bandGap=2.6374999999999993, eHull=0
- 8. mp-5777 (BaTiO3) score=0.900414, bandGap=2.2929999999999993, eHull=0
