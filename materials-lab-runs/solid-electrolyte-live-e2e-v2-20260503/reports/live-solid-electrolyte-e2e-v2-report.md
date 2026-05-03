# Live Materials Project Solid-State Electrolyte Candidate Screening V2

## Confidence Level

- Screening level: `proxy-screen`
- Warning: This is a proxy-screen validation run, not a validated solid-electrolyte discovery result.
- Warning: Li sublattice metrics are geometric descriptors, not measured or simulated ionic conductivity.
- Warning: This report is a proxy screen. It does not establish transport performance, electrochemical stability, or experimental viability.

## Research Goal

Validate the patched OpenClaw Materials Lab solid-electrolyte preset on live Materials Project data and check whether it produces a more diverse, better-labeled proxy shortlist.

## Evaluation Criteria

- Live Materials Project source only; offline fallback disabled.
- Energy above hull <= 0.1 eV for preliminary thermodynamic stability screening.
- Band gap is treated as a minimum electronic-insulation screen, not as a rigid target alignment.
- Density is advisory and not weighted in the solid-electrolyte preset.
- Formula diversity is enforced with maxPerFormula=1 and maxPerFamily=3.
- Top candidates must have retrievable structures for downstream Li proxy analysis.
- This run still does not compute ionic conductivity, migration barriers, electrochemical windows, or electrode interface reactivity.

## Candidate Table

| Rank | Material | Formula | Family | eHull eV | Gap eV | Density g/cm3 | Score | Flags |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | [mp-985583](https://materialsproject.org/materials/mp-985583) | Li3PS4 | thiophosphate-sulfide | 0 | 2.8091 | 1.85427 | 1 | duplicate-formula, warning |
| 2 | [mp-11175](https://materialsproject.org/materials/mp-11175) | LiZnPS4 | thiophosphate-sulfide | 0 | 2.7312 | 2.49727 | 1 | warning |
| 3 | [mp-760046](https://materialsproject.org/materials/mp-760046) | LiPH21S3N7 | thiophosphate-sulfide | 0 | 3.2702 | 1.22203 | 1 | warning |
| 4 | [mp-10499](https://materialsproject.org/materials/mp-10499) | LiZr2(PO4)3 | zirconium-phosphate | 0 | 4.2533 | 3.2197 | 1 | duplicate-formula, warning |
| 5 | [mp-1139957](https://materialsproject.org/materials/mp-1139957) | LiY(TlCl3)2 | halide | 0 | 4.4444 | 4.2784 | 1 | duplicate-formula, warning |
| 6 | [mp-567652](https://materialsproject.org/materials/mp-567652) | Cs2LiYCl6 | halide | 0 | 4.8986 | 3.17828 | 1 | warning |
| 7 | [mp-30301](https://materialsproject.org/materials/mp-30301) | LiClO4 | halide | 0 | 5.7447 | 2.55713 | 1 | warning |
| 8 | [mp-766132](https://materialsproject.org/materials/mp-766132) | Li2ZrFe(PO4)3 | zirconium-phosphate | 0.00301738 | 2.4566 | 3.04392 | 0.990194 | warning |
| 9 | [mp-1223569](https://materialsproject.org/materials/mp-1223569) | Li4Zr8V3(P3O16)3 | zirconium-phosphate | 0.00637703 | 3.1339 | 3.05728 | 0.979275 | warning |
| 10 | [mp-942733](https://materialsproject.org/materials/mp-942733) | Li7La3Zr2O12 | garnet-oxide | 0.00684601 | 4.1688 | 5.0131 | 0.97775 | - |
| 11 | [mp-769074](https://materialsproject.org/materials/mp-769074) | Na2LiTi3Al(PO4)6 | nasicon-oxide | 0.0128596 | 2.5293 | 2.83734 | 0.958206 | duplicate-formula, warning |
| 12 | [mp-696138](https://materialsproject.org/materials/mp-696138) | Li10Ge(PS6)2 | lgps-like-sulfide | 0.0187605 | 2.5395 | 1.97713 | 0.939028 | duplicate-formula, warning |

## Ranked Candidates

### 1. [mp-985583](https://materialsproject.org/materials/mp-985583) (Li3PS4)

- Score: 1
- Source: materials-project
- Family: thiophosphate-sulfide
- Space group: Pnma
- eHull: 0 eV
- Band gap: 2.8091 eV
- Density: 1.85427 g/cm3
- Duplicate group: Li3PS4 (3 candidate(s))
- Weighted stability: 0.65
- Weighted bandGap: 0.35
- Weighted density: 0
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.618 (not weighted)
- Warning: Duplicate reduced-formula group appears 3 times.
- Warning: Material family 'thiophosphate-sulfide' appears 23 times in the candidate pool.

### 2. [mp-11175](https://materialsproject.org/materials/mp-11175) (LiZnPS4)

- Score: 1
- Source: materials-project
- Family: thiophosphate-sulfide
- Space group: I-4
- eHull: 0 eV
- Band gap: 2.7312 eV
- Density: 2.49727 g/cm3
- Duplicate group: LiZnPS4 (1 candidate(s))
- Weighted stability: 0.65
- Weighted bandGap: 0.35
- Weighted density: 0
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.832 (not weighted)
- Warning: Material family 'thiophosphate-sulfide' appears 23 times in the candidate pool.

### 3. [mp-760046](https://materialsproject.org/materials/mp-760046) (LiPH21S3N7)

- Score: 1
- Source: materials-project
- Family: thiophosphate-sulfide
- Space group: P-1
- eHull: 0 eV
- Band gap: 3.2702 eV
- Density: 1.22203 g/cm3
- Duplicate group: LiPH21S3N7 (1 candidate(s))
- Weighted stability: 0.65
- Weighted bandGap: 0.35
- Weighted density: 0
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.407 (not weighted)
- Warning: Material family 'thiophosphate-sulfide' appears 23 times in the candidate pool.

### 4. [mp-10499](https://materialsproject.org/materials/mp-10499) (LiZr2(PO4)3)

- Score: 1
- Source: materials-project
- Family: zirconium-phosphate
- Space group: P2_1/c
- eHull: 0 eV
- Band gap: 4.2533 eV
- Density: 3.2197 g/cm3
- Duplicate group: LiZr2(PO4)3 (6 candidate(s))
- Weighted stability: 0.65
- Weighted bandGap: 0.35
- Weighted density: 0
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.927 (not weighted)
- Warning: Duplicate reduced-formula group appears 6 times.
- Warning: Material family 'zirconium-phosphate' appears 11 times in the candidate pool.

### 5. [mp-1139957](https://materialsproject.org/materials/mp-1139957) (LiY(TlCl3)2)

- Score: 1
- Source: materials-project
- Family: halide
- Space group: P-1
- eHull: 0 eV
- Band gap: 4.4444 eV
- Density: 4.2784 g/cm3
- Duplicate group: LiY(TlCl3)2 (2 candidate(s))
- Weighted stability: 0.65
- Weighted bandGap: 0.35
- Weighted density: 0
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.574 (not weighted)
- Warning: Duplicate reduced-formula group appears 2 times.
- Warning: Material family 'halide' appears 25 times in the candidate pool.

### 6. [mp-567652](https://materialsproject.org/materials/mp-567652) (Cs2LiYCl6)

- Score: 1
- Source: materials-project
- Family: halide
- Space group: Fm-3m
- eHull: 0 eV
- Band gap: 4.8986 eV
- Density: 3.17828 g/cm3
- Duplicate group: Cs2LiYCl6 (1 candidate(s))
- Weighted stability: 0.65
- Weighted bandGap: 0.35
- Weighted density: 0
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.941 (not weighted)
- Warning: Material family 'halide' appears 25 times in the candidate pool.

### 7. [mp-30301](https://materialsproject.org/materials/mp-30301) (LiClO4)

- Score: 1
- Source: materials-project
- Family: halide
- Space group: Pnma
- eHull: 0 eV
- Band gap: 5.7447 eV
- Density: 2.55713 g/cm3
- Duplicate group: LiClO4 (1 candidate(s))
- Weighted stability: 0.65
- Weighted bandGap: 0.35
- Weighted density: 0
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.852 (not weighted)
- Warning: Material family 'halide' appears 25 times in the candidate pool.

### 8. [mp-766132](https://materialsproject.org/materials/mp-766132) (Li2ZrFe(PO4)3)

- Score: 0.990194
- Source: materials-project
- Family: zirconium-phosphate
- Space group: Pna2_1
- eHull: 0.00301738 eV
- Band gap: 2.4566 eV
- Density: 3.04392 g/cm3
- Duplicate group: Li2ZrFe(PO4)3 (1 candidate(s))
- Weighted stability: 0.640194
- Weighted bandGap: 0.35
- Weighted density: 0
- stability score 0.985
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.985 (not weighted)
- Warning: Material family 'zirconium-phosphate' appears 11 times in the candidate pool.

### 9. [mp-1223569](https://materialsproject.org/materials/mp-1223569) (Li4Zr8V3(P3O16)3)

- Score: 0.979275
- Source: materials-project
- Family: zirconium-phosphate
- Space group: P1
- eHull: 0.00637703 eV
- Band gap: 3.1339 eV
- Density: 3.05728 g/cm3
- Duplicate group: Li4Zr8V3(P3O16)3 (1 candidate(s))
- Weighted stability: 0.629275
- Weighted bandGap: 0.35
- Weighted density: 0
- stability score 0.968
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.981 (not weighted)
- Warning: Material family 'zirconium-phosphate' appears 11 times in the candidate pool.

### 10. [mp-942733](https://materialsproject.org/materials/mp-942733) (Li7La3Zr2O12)

- Score: 0.97775
- Source: materials-project
- Family: garnet-oxide
- Space group: I4_1/acd
- eHull: 0.00684601 eV
- Band gap: 4.1688 eV
- Density: 5.0131 g/cm3
- Duplicate group: Li7La3Zr2O12 (1 candidate(s))
- Weighted stability: 0.62775
- Weighted bandGap: 0.35
- Weighted density: 0
- stability score 0.966
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.329 (not weighted)

### 11. [mp-769074](https://materialsproject.org/materials/mp-769074) (Na2LiTi3Al(PO4)6)

- Score: 0.958206
- Source: materials-project
- Family: nasicon-oxide
- Space group: P1
- eHull: 0.0128596 eV
- Band gap: 2.5293 eV
- Density: 2.83734 g/cm3
- Duplicate group: Na2LiTi3Al(PO4)6 (2 candidate(s))
- Weighted stability: 0.608206
- Weighted bandGap: 0.35
- Weighted density: 0
- stability score 0.936
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.946 (not weighted)
- Warning: Duplicate reduced-formula group appears 2 times.
- Warning: Material family 'nasicon-oxide' appears 4 times in the candidate pool.

### 12. [mp-696138](https://materialsproject.org/materials/mp-696138) (Li10Ge(PS6)2)

- Score: 0.939028
- Source: materials-project
- Family: lgps-like-sulfide
- Space group: P1
- eHull: 0.0187605 eV
- Band gap: 2.5395 eV
- Density: 1.97713 g/cm3
- Duplicate group: Li10Ge(PS6)2 (2 candidate(s))
- Weighted stability: 0.589028
- Weighted bandGap: 0.35
- Weighted density: 0
- stability score 0.906
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.659 (not weighted)
- Warning: Duplicate reduced-formula group appears 2 times.
- Warning: Material family 'lgps-like-sulfide' appears 2 times in the candidate pool.

## Method Notes

- Compared against the earlier E2E weakness where one formula family dominated the top ranks.
- Formula diversity was enabled to force a shortlist of distinct hypotheses.
- CSV and JSONL ranking artifacts were required for downstream researcher review.

## Provenance

- runRoot: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503
- generatedAt: 2026-05-03T07:10:26.434Z
- dataSource: Materials Project live API
- offlineFallbackAllowed: False
- compareCriteria: `{'preset': 'solid-electrolyte', 'screeningLevel': 'proxy-screen', 'stabilityWeight': 0.65, 'bandGapWeight': 0.35, 'densityWeight': 0, 'bandGapScoringMode': 'minimum', 'minimumBandGapEv': 2, 'bandGapTargetEv': 5, 'densityScoringMode': 'advisory', 'densityTargetGcm3': 3, 'diversifyBy': 'formula', 'maxPerFormula': 1, 'maxPerFamily': 3}`
- pluginPackageVersion: 0.1.0

## Notes

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/notes/2026-05-03T07-10-26-433Z-live-materials-project-solid-state-electrolyte-screening-v2-proc.md

## Artifacts

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/plots/solid-electrolyte-ranking-v2/candidate-ranking.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/plots/solid-electrolyte-ranking-v2/candidate-ranking.csv
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/plots/solid-electrolyte-ranking-v2/candidate-ranking.jsonl
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-985583/mp-985583.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-985583/mp-985583.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-985583/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-11175/mp-11175.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-11175/mp-11175.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-11175/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-760046/mp-760046.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-760046/mp-760046.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-760046/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-10499/mp-10499.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-10499/mp-10499.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-10499/structure-metrics.png

## Limitations

- Ranking depends on the chosen criteria and available data.
- Offline/mock mode should not be treated as equivalent to live database validation.
- Domain-specific properties such as ion mobility, defect chemistry, electrochemical windows, and interface reactivity require additional calculations or experiments.

