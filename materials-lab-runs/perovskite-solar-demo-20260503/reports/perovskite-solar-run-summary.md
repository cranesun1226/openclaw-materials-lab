# Perovskite Solar Materials Exploration Run Summary

Generated: 2026-05-03T05:34:53.104Z

## Question

Can we identify a stable perovskite or perovskite-adjacent solar absorber candidate with a band gap near 1.1-2.2 eV using the current Materials Lab OpenClaw plugin?

## Execution Mode

- OpenClaw Materials Lab plugin path: local repository build
- Materials Project API key configured: false
- Data mode used by searches: offline/mock fallback
- Python worker: /Users/haksunlee/.pyenv/versions/3.14.3/bin/python3

## Process

1. Ran an exact halide-perovskite style search for Pb + I candidates with band gap 1.0-2.2 eV and hull energy <= 0.1 eV.
2. The exact halide query returned 0 candidates in offline/mock mode.
3. Broadened the search to the available oxide perovskite reference SrTiO3.
4. Added stable mock materials in a solar-relevant band-gap window so the comparison tool had a meaningful ranking set.
5. Ranked candidates with target band gap 1.5 eV and weights: stability 0.45, band gap 0.45, density 0.1.
6. Fetched and analyzed the SrTiO3 structure to verify structure artifact generation and local analysis.
7. Saved a process note and exported the standard plugin report.

## Candidate Ranking

| Rank | Material ID | Formula | Score | Hull eV | Band gap eV | Source | Reasons |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| 1 | mp-mock-si | Si | 0.8326 | 0 | 1.12 | mock | stability score 1.000; band-gap alignment 0.747; density alignment 0.466 |
| 2 | mp-mock-lifepo4 | LiFePO4 | 0.522 | 0 | 3.8 | mock | stability score 1.000; band-gap alignment 0.000; density alignment 0.720 |
| 3 | mp-mock-srtio3 | SrTiO3 | 0.5208 | 0.012 | 3.25 | mock | stability score 0.940; band-gap alignment 0.000; density alignment 0.978 |

## SrTiO3 Structure Analysis

SrTiO3 fallback analysis found 3 listed sites and elements O, Sr, Ti.

Summary metrics:

```json
{
  "formula": "SrTiO3",
  "numSites": 3,
  "volume": 59.5474,
  "a": 3.905,
  "b": 3.905,
  "c": 3.905,
  "numElements": 3
}
```

## Interpretation

- The run successfully exercised search, candidate comparison, structure fetch, structure analysis, note writing, and report export.
- No true halide perovskite absorber was found because the current run had no Materials Project API key and the bundled offline dataset is intentionally small.
- SrTiO3 is useful here as a perovskite oxide workflow reference, but its mock band gap of 3.25 eV is too wide for a main single-junction absorber target.
- Si ranks well because its band gap is close to the chosen photovoltaic target, but it is not a perovskite.

## Generated Files

- Process note: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-demo-20260503/notes/2026-05-03T05-34-53-058Z-perovskite-solar-materials-exploration-process-note.md
- Standard plugin report: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-demo-20260503/reports/perovskite-solar-standard-report.md
- Artifact: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/perovskite-solar-demo-20260503/structures/mp-mock-srtio3/mp-mock-srtio3.json

## Warnings And Limitations

- Using offline mock data.
- Using offline mock data.
- Using offline mock data.
- CIF export was skipped because pymatgen is unavailable for this structure.
- Metric plot was skipped because matplotlib is unavailable.
- Candidate ranking plot was skipped because matplotlib is unavailable.
- This is a workflow validation run, not a live scientific screening result. For real perovskite solar discovery, configure mpApiKey and query Pb/Sn/I/Br/Cl compositions directly.
