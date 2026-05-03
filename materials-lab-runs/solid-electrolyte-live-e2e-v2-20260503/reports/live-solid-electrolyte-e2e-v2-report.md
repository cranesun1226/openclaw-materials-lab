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
- Secondary tie-breaker scoring uses composition-level Li fraction, family priors, band-gap margin, and chemistry-risk signals.
- Toxic/high-risk elements and molecular-salt-like compositions are filtered or penalized by default.
- Formula diversity is enforced with maxPerFormula=1 and maxPerFamily=3.
- Structures are selected with a family-balanced pass before downstream Li proxy analysis.
- This run still does not compute ionic conductivity, migration barriers, electrochemical windows, or electrode interface reactivity.

## Candidate Table

| Rank | Material | Formula | Family | eHull eV | Gap eV | Score | Secondary | Risk | Flags |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | [mp-556886](https://materialsproject.org/materials/mp-556886) | Li4Al3Ge3ClO12 | halide | 0.000452765 | 4.1175 | 0.994341 | 0.956656 | 0 | warning |
| 2 | [mp-554203](https://materialsproject.org/materials/mp-554203) | Li4Ga3Si3ClO12 | halide | 0 | 4.5903 | 0.992711 | 0.927106 | 0 | warning |
| 3 | [mp-567652](https://materialsproject.org/materials/mp-567652) | Cs2LiYCl6 | halide | 0 | 4.8986 | 0.990784 | 0.907837 | 0 | warning |
| 4 | [mp-985583](https://materialsproject.org/materials/mp-985583) | Li3PS4 | thiophosphate-sulfide | 0 | 2.8091 | 0.989557 | 0.895569 | 0 | duplicate-formula, warning |
| 5 | [mp-11175](https://materialsproject.org/materials/mp-11175) | LiZnPS4 | thiophosphate-sulfide | 0 | 2.7312 | 0.98907 | 0.8907 | 0 | warning |
| 6 | [mp-950995](https://materialsproject.org/materials/mp-950995) | Li6PS5I | thiophosphate-sulfide | 0.00212493 | 2.5333 | 0.980849 | 0.870639 | 0 | duplicate-formula, warning |
| 7 | [mp-10499](https://materialsproject.org/materials/mp-10499) | LiZr2(PO4)3 | zirconium-phosphate | 0 | 4.2533 | 0.978484 | 0.784837 | 0 | duplicate-formula, warning |
| 8 | [mp-942733](https://materialsproject.org/materials/mp-942733) | Li7La3Zr2O12 | garnet-oxide | 0.00684601 | 4.1688 | 0.97742 | 0.97445 | 0 | - |
| 9 | [mp-766132](https://materialsproject.org/materials/mp-766132) | Li2ZrFe(PO4)3 | zirconium-phosphate | 0.00301738 | 2.4566 | 0.974928 | 0.837537 | 0 | warning |
| 10 | [mp-1223569](https://materialsproject.org/materials/mp-1223569) | Li4Zr8V3(P3O16)3 | zirconium-phosphate | 0.00637703 | 3.1339 | 0.956001 | 0.746537 | 0 | warning |
| 11 | [mp-696138](https://materialsproject.org/materials/mp-696138) | Li10Ge(PS6)2 | lgps-like-sulfide | 0.0187605 | 2.5395 | 0.935997 | 0.908719 | 0 | duplicate-formula, warning |
| 12 | [mp-769074](https://materialsproject.org/materials/mp-769074) | Na2LiTi3Al(PO4)6 | nasicon-oxide | 0.0128596 | 2.5293 | 0.928902 | 0.665162 | 0 | duplicate-formula, warning |

## Ranked Candidates

### 1. [mp-556886](https://materialsproject.org/materials/mp-556886) (Li4Al3Ge3ClO12)

- Score: 0.994341
- Primary score: 0.998529
- Secondary score: 0.956656
- Risk penalty: 0
- Source: materials-project
- Family: halide
- Space group: P-43n
- eHull: 0.000452765 eV
- Band gap: 4.1175 eV
- Density: 2.77709 g/cm3
- Duplicate group: Li4Al3Ge3ClO12 (1 candidate(s))
- Risk flags: -
- Weighted stability: 0.583676
- Weighted bandGap: 0.315
- Weighted density: 0
- Weighted secondary: 0.095666
- stability score 0.998
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.926 (not weighted)
- secondary tie-breaker 0.957 (Li fraction 1.000, family prior 0.880, gap margin 0.971)
- Warning: Material family 'halide' appears 8 times in the candidate pool.

### 2. [mp-554203](https://materialsproject.org/materials/mp-554203) (Li4Ga3Si3ClO12)

- Score: 0.992711
- Primary score: 1
- Secondary score: 0.927106
- Risk penalty: 0
- Source: materials-project
- Family: halide
- Space group: P-43n
- eHull: 0 eV
- Band gap: 4.5903 eV
- Density: 2.84933 g/cm3
- Duplicate group: Li4Ga3Si3ClO12 (1 candidate(s))
- Risk flags: -
- Weighted stability: 0.585
- Weighted bandGap: 0.315
- Weighted density: 0
- Weighted secondary: 0.092711
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.950 (not weighted)
- secondary tie-breaker 0.927 (Li fraction 1.000, family prior 0.880, gap margin 0.852)
- Warning: Material family 'halide' appears 8 times in the candidate pool.

### 3. [mp-567652](https://materialsproject.org/materials/mp-567652) (Cs2LiYCl6)

- Score: 0.990784
- Primary score: 1
- Secondary score: 0.907837
- Risk penalty: 0
- Source: materials-project
- Family: halide
- Space group: Fm-3m
- eHull: 0 eV
- Band gap: 4.8986 eV
- Density: 3.17828 g/cm3
- Duplicate group: Cs2LiYCl6 (1 candidate(s))
- Risk flags: -
- Weighted stability: 0.585
- Weighted bandGap: 0.315
- Weighted density: 0
- Weighted secondary: 0.090784
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.941 (not weighted)
- secondary tie-breaker 0.908 (Li fraction 1.000, family prior 0.880, gap margin 0.775)
- Warning: Material family 'halide' appears 8 times in the candidate pool.

### 4. [mp-985583](https://materialsproject.org/materials/mp-985583) (Li3PS4)

- Score: 0.989557
- Primary score: 1
- Secondary score: 0.895569
- Risk penalty: 0
- Source: materials-project
- Family: thiophosphate-sulfide
- Space group: Pnma
- eHull: 0 eV
- Band gap: 2.8091 eV
- Density: 1.85427 g/cm3
- Duplicate group: Li3PS4 (3 candidate(s))
- Risk flags: -
- Weighted stability: 0.585
- Weighted bandGap: 0.315
- Weighted density: 0
- Weighted secondary: 0.089557
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.618 (not weighted)
- secondary tie-breaker 0.896 (Li fraction 1.000, family prior 0.900, gap margin 0.702)
- Warning: Duplicate reduced-formula group appears 3 times.
- Warning: Material family 'thiophosphate-sulfide' appears 22 times in the candidate pool.

### 5. [mp-11175](https://materialsproject.org/materials/mp-11175) (LiZnPS4)

- Score: 0.98907
- Primary score: 1
- Secondary score: 0.8907
- Risk penalty: 0
- Source: materials-project
- Family: thiophosphate-sulfide
- Space group: I-4
- eHull: 0 eV
- Band gap: 2.7312 eV
- Density: 2.49727 g/cm3
- Duplicate group: LiZnPS4 (1 candidate(s))
- Risk flags: -
- Weighted stability: 0.585
- Weighted bandGap: 0.315
- Weighted density: 0
- Weighted secondary: 0.08907
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.832 (not weighted)
- secondary tie-breaker 0.891 (Li fraction 1.000, family prior 0.900, gap margin 0.683)
- Warning: Material family 'thiophosphate-sulfide' appears 22 times in the candidate pool.

### 6. [mp-950995](https://materialsproject.org/materials/mp-950995) (Li6PS5I)

- Score: 0.980849
- Primary score: 0.993094
- Secondary score: 0.870639
- Risk penalty: 0
- Source: materials-project
- Family: thiophosphate-sulfide
- Space group: Cc
- eHull: 0.00212493 eV
- Band gap: 2.5333 eV
- Density: 2.221 g/cm3
- Duplicate group: Li6PS5I (2 candidate(s))
- Risk flags: -
- Weighted stability: 0.578785
- Weighted bandGap: 0.315
- Weighted density: 0
- Weighted secondary: 0.087064
- stability score 0.989
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.740 (not weighted)
- secondary tie-breaker 0.871 (Li fraction 0.974, family prior 0.900, gap margin 0.633)
- Warning: Duplicate reduced-formula group appears 2 times.
- Warning: Material family 'thiophosphate-sulfide' appears 22 times in the candidate pool.

### 7. [mp-10499](https://materialsproject.org/materials/mp-10499) (LiZr2(PO4)3)

- Score: 0.978484
- Primary score: 1
- Secondary score: 0.784837
- Risk penalty: 0
- Source: materials-project
- Family: zirconium-phosphate
- Space group: P2_1/c
- eHull: 0 eV
- Band gap: 4.2533 eV
- Density: 3.2197 g/cm3
- Duplicate group: LiZr2(PO4)3 (6 candidate(s))
- Risk flags: -
- Weighted stability: 0.585
- Weighted bandGap: 0.315
- Weighted density: 0
- Weighted secondary: 0.078484
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.927 (not weighted)
- secondary tie-breaker 0.785 (Li fraction 0.556, family prior 0.780, gap margin 0.937)
- Warning: Duplicate reduced-formula group appears 6 times.
- Warning: Material family 'zirconium-phosphate' appears 11 times in the candidate pool.

### 8. [mp-942733](https://materialsproject.org/materials/mp-942733) (Li7La3Zr2O12)

- Score: 0.97742
- Primary score: 0.97775
- Secondary score: 0.97445
- Risk penalty: 0
- Source: materials-project
- Family: garnet-oxide
- Space group: I4_1/acd
- eHull: 0.00684601 eV
- Band gap: 4.1688 eV
- Density: 5.0131 g/cm3
- Duplicate group: Li7La3Zr2O12 (1 candidate(s))
- Risk flags: -
- Weighted stability: 0.564975
- Weighted bandGap: 0.315
- Weighted density: 0
- Weighted secondary: 0.097445
- stability score 0.966
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.329 (not weighted)
- secondary tie-breaker 0.974 (Li fraction 1.000, family prior 0.950, gap margin 0.958)

### 9. [mp-766132](https://materialsproject.org/materials/mp-766132) (Li2ZrFe(PO4)3)

- Score: 0.974928
- Primary score: 0.990194
- Secondary score: 0.837537
- Risk penalty: 0
- Source: materials-project
- Family: zirconium-phosphate
- Space group: Pna2_1
- eHull: 0.00301738 eV
- Band gap: 2.4566 eV
- Density: 3.04392 g/cm3
- Duplicate group: Li2ZrFe(PO4)3 (1 candidate(s))
- Risk flags: -
- Weighted stability: 0.576174
- Weighted bandGap: 0.315
- Weighted density: 0
- Weighted secondary: 0.083754
- stability score 0.985
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.985 (not weighted)
- secondary tie-breaker 0.838 (Li fraction 1.000, family prior 0.780, gap margin 0.614)
- Warning: Material family 'zirconium-phosphate' appears 11 times in the candidate pool.

### 10. [mp-1223569](https://materialsproject.org/materials/mp-1223569) (Li4Zr8V3(P3O16)3)

- Score: 0.956001
- Primary score: 0.979275
- Secondary score: 0.746537
- Risk penalty: 0
- Source: materials-project
- Family: zirconium-phosphate
- Space group: P1
- eHull: 0.00637703 eV
- Band gap: 3.1339 eV
- Density: 3.05728 g/cm3
- Duplicate group: Li4Zr8V3(P3O16)3 (1 candidate(s))
- Risk flags: -
- Weighted stability: 0.566347
- Weighted bandGap: 0.315
- Weighted density: 0
- Weighted secondary: 0.074654
- stability score 0.968
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.981 (not weighted)
- secondary tie-breaker 0.747 (Li fraction 0.556, family prior 0.780, gap margin 0.783)
- Warning: Material family 'zirconium-phosphate' appears 11 times in the candidate pool.

### 11. [mp-696138](https://materialsproject.org/materials/mp-696138) (Li10Ge(PS6)2)

- Score: 0.935997
- Primary score: 0.939028
- Secondary score: 0.908719
- Risk penalty: 0
- Source: materials-project
- Family: lgps-like-sulfide
- Space group: P1
- eHull: 0.0187605 eV
- Band gap: 2.5395 eV
- Density: 1.97713 g/cm3
- Duplicate group: Li10Ge(PS6)2 (2 candidate(s))
- Risk flags: -
- Weighted stability: 0.530125
- Weighted bandGap: 0.315
- Weighted density: 0
- Weighted secondary: 0.090872
- stability score 0.906
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.659 (not weighted)
- secondary tie-breaker 0.909 (Li fraction 1.000, family prior 1.000, gap margin 0.635)
- Warning: Duplicate reduced-formula group appears 2 times.
- Warning: Material family 'lgps-like-sulfide' appears 2 times in the candidate pool.

### 12. [mp-769074](https://materialsproject.org/materials/mp-769074) (Na2LiTi3Al(PO4)6)

- Score: 0.928902
- Primary score: 0.958206
- Secondary score: 0.665162
- Risk penalty: 0
- Source: materials-project
- Family: nasicon-oxide
- Space group: P1
- eHull: 0.0128596 eV
- Band gap: 2.5293 eV
- Density: 2.83734 g/cm3
- Duplicate group: Na2LiTi3Al(PO4)6 (2 candidate(s))
- Risk flags: -
- Weighted stability: 0.547386
- Weighted bandGap: 0.315
- Weighted density: 0
- Weighted secondary: 0.066516
- stability score 0.936
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.946 (not weighted)
- secondary tie-breaker 0.665 (Li fraction 0.270, family prior 0.920, gap margin 0.632)
- Warning: Duplicate reduced-formula group appears 2 times.
- Warning: Material family 'nasicon-oxide' appears 4 times in the candidate pool.

## Why Candidates Might Fail

| Rank | Material | Main Failure Risks |
| ---: | --- | --- |
| 1 | [mp-556886](https://materialsproject.org/materials/mp-556886) | Material family 'halide' appears 8 times in the candidate pool. |
| 2 | [mp-554203](https://materialsproject.org/materials/mp-554203) | Material family 'halide' appears 8 times in the candidate pool. |
| 3 | [mp-567652](https://materialsproject.org/materials/mp-567652) | Material family 'halide' appears 8 times in the candidate pool. |
| 4 | [mp-985583](https://materialsproject.org/materials/mp-985583) | Duplicate reduced-formula group appears 3 times.; Material family 'thiophosphate-sulfide' appears 22 times in the candidate pool. |
| 5 | [mp-11175](https://materialsproject.org/materials/mp-11175) | Material family 'thiophosphate-sulfide' appears 22 times in the candidate pool. |
| 6 | [mp-950995](https://materialsproject.org/materials/mp-950995) | Duplicate reduced-formula group appears 2 times.; Material family 'thiophosphate-sulfide' appears 22 times in the candidate pool. |
| 7 | [mp-10499](https://materialsproject.org/materials/mp-10499) | Duplicate reduced-formula group appears 6 times.; Material family 'zirconium-phosphate' appears 11 times in the candidate pool. |
| 8 | [mp-942733](https://materialsproject.org/materials/mp-942733) | No heuristic risk flag; still needs transport and electrochemical validation. |
| 9 | [mp-766132](https://materialsproject.org/materials/mp-766132) | Material family 'zirconium-phosphate' appears 11 times in the candidate pool. |
| 10 | [mp-1223569](https://materialsproject.org/materials/mp-1223569) | Material family 'zirconium-phosphate' appears 11 times in the candidate pool. |
| 11 | [mp-696138](https://materialsproject.org/materials/mp-696138) | Duplicate reduced-formula group appears 2 times.; Material family 'lgps-like-sulfide' appears 2 times in the candidate pool. |
| 12 | [mp-769074](https://materialsproject.org/materials/mp-769074) | Duplicate reduced-formula group appears 2 times.; Material family 'nasicon-oxide' appears 4 times in the candidate pool. |

## Method Notes

- Compared against the earlier E2E weakness where one formula family dominated the top ranks.
- Formula diversity was enabled to force a shortlist of distinct hypotheses.
- Family-balanced structure selection was enabled to avoid analyzing only the first ranked family.
- CSV and JSONL ranking artifacts were required for downstream researcher review.

## Provenance

- runRoot: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503
- generatedAt: 2026-05-03T07:21:11.520Z
- dataSource: Materials Project live API
- offlineFallbackAllowed: False
- compareCriteria: `{'preset': 'solid-electrolyte', 'screeningLevel': 'proxy-screen', 'stabilityWeight': 0.65, 'bandGapWeight': 0.35, 'densityWeight': 0, 'bandGapScoringMode': 'minimum', 'minimumBandGapEv': 2, 'bandGapTargetEv': 5, 'densityScoringMode': 'advisory', 'densityTargetGcm3': 3, 'secondaryWeight': 0.1, 'riskPenaltyWeight': 0.3, 'preferredBandGapEv': 4, 'preferredLiFractionMin': 0.1, 'preferredLiFractionMax': 0.45, 'excludeToxicElements': True, 'excludeRiskyChemistry': True, 'filterMolecularSalts': True, 'excludedElements': ['Be', 'Cd', 'Hg', 'Pb', 'Tl', 'Th', 'U'], 'flaggedElements': ['As', 'Cr', 'Sb', 'Se'], 'maxHydrogenAtomicFraction': 0.15, 'diversifyBy': 'formula', 'maxPerFormula': 1, 'maxPerFamily': 3}`
- pluginPackageVersion: 0.1.0

## Notes

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/notes/2026-05-03T07-21-11-519Z-live-materials-project-solid-state-electrolyte-screening-v2-proc.md

## Artifacts

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/plots/solid-electrolyte-ranking-v2/candidate-ranking.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/plots/solid-electrolyte-ranking-v2/candidate-ranking.csv
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/plots/solid-electrolyte-ranking-v2/candidate-ranking.jsonl
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-556886/mp-556886.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-556886/mp-556886.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-556886/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-985583/mp-985583.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-985583/mp-985583.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-985583/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-10499/mp-10499.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-10499/mp-10499.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-10499/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-942733/mp-942733.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-942733/mp-942733.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/structures/mp-942733/structure-metrics.png

## Limitations

- Ranking depends on the chosen criteria and available data.
- Offline/mock mode should not be treated as equivalent to live database validation.
- Domain-specific properties such as ion mobility, defect chemistry, electrochemical windows, and interface reactivity require additional calculations or experiments.

