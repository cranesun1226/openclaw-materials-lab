# Live Materials Project High-k Dielectric Oxide Proxy Screening

## Confidence Level

- Screening level: `proxy-screen`
- Warning: This is a proxy-screen validation run, not a validated gate-dielectric discovery result.
- Warning: The current plugin does not fetch or compute dielectric tensors, band offsets, leakage barriers, or interface stability.
- Warning: This report is a proxy screen. It does not establish transport performance, electrochemical stability, or experimental viability.

## Research Goal

Use OpenClaw Materials Lab with live Materials Project data to validate a non-battery proxy workflow for stable wide-bandgap oxide gate-dielectric candidates.

## Evaluation Criteria

- Live Materials Project source only; offline fallback disabled.
- Energy above hull <= 0.08 eV for preliminary thermodynamic stability screening.
- Band gap ranked toward 5.5 eV as a proxy for low leakage and insulating behavior.
- Density ranked toward 6.0 g/cm3 as a weak proxy for heavy-cation oxide dielectric families.
- Formula diversity is enforced with maxPerFormula=1.
- This run does not compute dielectric constant, band offsets to Si, leakage current, phonon stability, amorphizability, or interface reactions.

## Candidate Table

| Rank | Material | Formula | Family | eHull eV | Gap eV | Score | Secondary | Risk | Flags |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | [mp-1143](https://materialsproject.org/materials/mp-1143) | Al2O3 | generic | 0 | 5.8537 | 0.921114 | 0.582192 | 0 | duplicate-formula, warning |
| 2 | [mp-733790](https://materialsproject.org/materials/mp-733790) | SiO2 | generic | 0.0065735 | 5.5868 | 0.885272 | 0.604433 | 0 | duplicate-formula, warning |
| 3 | [mp-2652](https://materialsproject.org/materials/mp-2652) | Y2O3 | generic | 0 | 4.0973 | 0.873639 | 0.728558 | 0 | duplicate-formula, warning |
| 4 | [mp-1968](https://materialsproject.org/materials/mp-1968) | La2O3 | generic | 0 | 3.8248 | 0.862787 | 0.751267 | 0 | duplicate-formula, warning |
| 5 | [mp-2858](https://materialsproject.org/materials/mp-2858) | ZrO2 | generic | 0 | 3.5322 | 0.851321 | 0.77565 | 0 | duplicate-formula, warning |
| 6 | [mp-352](https://materialsproject.org/materials/mp-352) | HfO2 | generic | 0 | 4.0165 | 0.786078 | 0.735292 | 0 | duplicate-formula, warning |
| 7 | [mp-5020](https://materialsproject.org/materials/mp-5020) | BaTiO3 | generic | 4.099e-05 | 2.5087 | 0.779849 | 0.779058 | 0 | duplicate-formula, warning |
| 8 | [mp-1439](https://materialsproject.org/materials/mp-1439) | TiO2 | generic | 0.0045236 | 2.5281 | 0.731361 | 0.780675 | 0 | duplicate-formula, warning |
| 9 | [mp-1238961](https://materialsproject.org/materials/mp-1238961) | Ta2O5 | generic | 0.0139272 | 2.341 | 0.699562 | 0.765083 | 0 | duplicate-formula, warning |

## Ranked Candidates

### 1. [mp-1143](https://materialsproject.org/materials/mp-1143) (Al2O3)

- Score: 0.921114
- Primary score: 0.921114
- Secondary score: 0.582192
- Risk penalty: 0
- Source: materials-project
- Family: generic
- Space group: R-3c
- eHull: 0 eV
- Band gap: 5.8537 eV
- Density: 3.8735 g/cm3
- Duplicate group: Al2O3 (10 candidate(s))
- Risk flags: -
- Weighted stability: 0.45
- Weighted bandGap: 0.374276
- Weighted density: 0.096837
- Weighted secondary: 0
- stability score 1.000
- band-gap alignment 0.936 (target 5.5 eV)
- density alignment 0.646 (target 6.0 g/cm3)
- Warning: Duplicate reduced-formula group appears 10 times.
- Warning: Material family 'generic' appears 72 times in the candidate pool.

### 2. [mp-733790](https://materialsproject.org/materials/mp-733790) (SiO2)

- Score: 0.885272
- Primary score: 0.885272
- Secondary score: 0.604433
- Risk penalty: 0
- Source: materials-project
- Family: generic
- Space group: P1
- eHull: 0.0065735 eV
- Band gap: 5.5868 eV
- Density: 2.255 g/cm3
- Duplicate group: SiO2 (12 candidate(s))
- Risk flags: -
- Weighted stability: 0.43521
- Weighted bandGap: 0.393687
- Weighted density: 0.056375
- Weighted secondary: 0
- stability score 0.967
- band-gap alignment 0.984 (target 5.5 eV)
- density alignment 0.376 (target 6.0 g/cm3)
- Warning: Duplicate reduced-formula group appears 12 times.
- Warning: Material family 'generic' appears 72 times in the candidate pool.

### 3. [mp-2652](https://materialsproject.org/materials/mp-2652) (Y2O3)

- Score: 0.873639
- Primary score: 0.873639
- Secondary score: 0.728558
- Risk penalty: 0
- Source: materials-project
- Family: generic
- Space group: Ia-3
- eHull: 0 eV
- Band gap: 4.0973 eV
- Density: 5.02612 g/cm3
- Duplicate group: Y2O3 (6 candidate(s))
- Risk flags: -
- Weighted stability: 0.45
- Weighted bandGap: 0.297985
- Weighted density: 0.125653
- Weighted secondary: 0
- stability score 1.000
- band-gap alignment 0.745 (target 5.5 eV)
- density alignment 0.838 (target 6.0 g/cm3)
- Warning: Duplicate reduced-formula group appears 6 times.
- Warning: Material family 'generic' appears 72 times in the candidate pool.

### 4. [mp-1968](https://materialsproject.org/materials/mp-1968) (La2O3)

- Score: 0.862787
- Primary score: 0.862787
- Secondary score: 0.751267
- Risk penalty: 0
- Source: materials-project
- Family: generic
- Space group: P-3m1
- eHull: 0 eV
- Band gap: 3.8248 eV
- Density: 6.61523 g/cm3
- Duplicate group: La2O3 (3 candidate(s))
- Risk flags: -
- Weighted stability: 0.45
- Weighted bandGap: 0.278167
- Weighted density: 0.134619
- Weighted secondary: 0
- stability score 1.000
- band-gap alignment 0.695 (target 5.5 eV)
- density alignment 0.897 (target 6.0 g/cm3)
- Warning: Duplicate reduced-formula group appears 3 times.
- Warning: Material family 'generic' appears 72 times in the candidate pool.

### 5. [mp-2858](https://materialsproject.org/materials/mp-2858) (ZrO2)

- Score: 0.851321
- Primary score: 0.851321
- Secondary score: 0.77565
- Risk penalty: 0
- Source: materials-project
- Family: generic
- Space group: P2_1/c
- eHull: 0 eV
- Band gap: 3.5322 eV
- Density: 5.77733 g/cm3
- Duplicate group: ZrO2 (12 candidate(s))
- Risk flags: -
- Weighted stability: 0.45
- Weighted bandGap: 0.256887
- Weighted density: 0.144433
- Weighted secondary: 0
- stability score 1.000
- band-gap alignment 0.642 (target 5.5 eV)
- density alignment 0.963 (target 6.0 g/cm3)
- Warning: Duplicate reduced-formula group appears 12 times.
- Warning: Material family 'generic' appears 72 times in the candidate pool.

### 6. [mp-352](https://materialsproject.org/materials/mp-352) (HfO2)

- Score: 0.786078
- Primary score: 0.786078
- Secondary score: 0.735292
- Risk penalty: 0
- Source: materials-project
- Family: generic
- Space group: P2_1/c
- eHull: 0 eV
- Band gap: 4.0165 eV
- Density: 10.2412 g/cm3
- Duplicate group: HfO2 (7 candidate(s))
- Risk flags: -
- Weighted stability: 0.45
- Weighted bandGap: 0.292109
- Weighted density: 0.043969
- Weighted secondary: 0
- stability score 1.000
- band-gap alignment 0.730 (target 5.5 eV)
- density alignment 0.293 (target 6.0 g/cm3)
- Warning: Duplicate reduced-formula group appears 7 times.
- Warning: Material family 'generic' appears 72 times in the candidate pool.

### 7. [mp-5020](https://materialsproject.org/materials/mp-5020) (BaTiO3)

- Score: 0.779849
- Primary score: 0.779849
- Secondary score: 0.779058
- Risk penalty: 0
- Source: materials-project
- Family: generic
- Space group: R3m
- eHull: 4.099e-05 eV
- Band gap: 2.5087 eV
- Density: 5.89961 g/cm3
- Duplicate group: BaTiO3 (3 candidate(s))
- Risk flags: -
- Weighted stability: 0.449908
- Weighted bandGap: 0.182451
- Weighted density: 0.14749
- Weighted secondary: 0
- stability score 1.000
- band-gap alignment 0.456 (target 5.5 eV)
- density alignment 0.983 (target 6.0 g/cm3)
- Warning: Duplicate reduced-formula group appears 3 times.
- Warning: Material family 'generic' appears 72 times in the candidate pool.

### 8. [mp-1439](https://materialsproject.org/materials/mp-1439) (TiO2)

- Score: 0.731361
- Primary score: 0.731361
- Secondary score: 0.780675
- Risk penalty: 0
- Source: materials-project
- Family: generic
- Space group: Pbcn
- eHull: 0.0045236 eV
- Band gap: 2.5281 eV
- Density: 4.30708 g/cm3
- Duplicate group: TiO2 (12 candidate(s))
- Risk flags: -
- Weighted stability: 0.439822
- Weighted bandGap: 0.183862
- Weighted density: 0.107677
- Weighted secondary: 0
- stability score 0.977
- band-gap alignment 0.460 (target 5.5 eV)
- density alignment 0.718 (target 6.0 g/cm3)
- Warning: Duplicate reduced-formula group appears 12 times.
- Warning: Material family 'generic' appears 72 times in the candidate pool.

### 9. [mp-1238961](https://materialsproject.org/materials/mp-1238961) (Ta2O5)

- Score: 0.699562
- Primary score: 0.699562
- Secondary score: 0.765083
- Risk penalty: 0
- Source: materials-project
- Family: generic
- Space group: P2/m
- eHull: 0.0139272 eV
- Band gap: 2.341 eV
- Density: 7.57424 g/cm3
- Duplicate group: Ta2O5 (7 candidate(s))
- Risk flags: -
- Weighted stability: 0.418664
- Weighted bandGap: 0.170255
- Weighted density: 0.110644
- Weighted secondary: 0
- stability score 0.930
- band-gap alignment 0.426 (target 5.5 eV)
- density alignment 0.738 (target 6.0 g/cm3)
- Warning: Duplicate reduced-formula group appears 7 times.
- Warning: Material family 'generic' appears 72 times in the candidate pool.

## Why Candidates Might Fail

| Rank | Material | Main Failure Risks |
| ---: | --- | --- |
| 1 | [mp-1143](https://materialsproject.org/materials/mp-1143) | Duplicate reduced-formula group appears 10 times.; Material family 'generic' appears 72 times in the candidate pool. |
| 2 | [mp-733790](https://materialsproject.org/materials/mp-733790) | Duplicate reduced-formula group appears 12 times.; Material family 'generic' appears 72 times in the candidate pool. |
| 3 | [mp-2652](https://materialsproject.org/materials/mp-2652) | Duplicate reduced-formula group appears 6 times.; Material family 'generic' appears 72 times in the candidate pool. |
| 4 | [mp-1968](https://materialsproject.org/materials/mp-1968) | Duplicate reduced-formula group appears 3 times.; Material family 'generic' appears 72 times in the candidate pool. |
| 5 | [mp-2858](https://materialsproject.org/materials/mp-2858) | Duplicate reduced-formula group appears 12 times.; Material family 'generic' appears 72 times in the candidate pool. |
| 6 | [mp-352](https://materialsproject.org/materials/mp-352) | Duplicate reduced-formula group appears 7 times.; Material family 'generic' appears 72 times in the candidate pool. |
| 7 | [mp-5020](https://materialsproject.org/materials/mp-5020) | Duplicate reduced-formula group appears 3 times.; Material family 'generic' appears 72 times in the candidate pool. |
| 8 | [mp-1439](https://materialsproject.org/materials/mp-1439) | Duplicate reduced-formula group appears 12 times.; Material family 'generic' appears 72 times in the candidate pool. |
| 9 | [mp-1238961](https://materialsproject.org/materials/mp-1238961) | Duplicate reduced-formula group appears 7 times.; Material family 'generic' appears 72 times in the candidate pool. |

## Method Notes

- This E2E intentionally uses a non-Li, non-battery topic to test whether the plugin generalizes beyond solid electrolytes.
- Ranking is based on generic Materials Project summary fields and should be treated as a triage view only.

## Provenance

- runRoot: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503
- generatedAt: 2026-05-03T07:32:18.487Z
- dataSource: Materials Project live API
- offlineFallbackAllowed: False
- compareCriteria: `{'preset': 'generic', 'screeningLevel': 'proxy-screen', 'stabilityWeight': 0.45, 'bandGapWeight': 0.4, 'densityWeight': 0.15, 'bandGapScoringMode': 'target', 'minimumBandGapEv': 0, 'bandGapTargetEv': 5.5, 'densityScoringMode': 'target', 'densityTargetGcm3': 6, 'secondaryWeight': 0, 'riskPenaltyWeight': 0, 'preferredBandGapEv': 3, 'preferredLiFractionMin': 0, 'preferredLiFractionMax': 1, 'excludeToxicElements': False, 'excludeRiskyChemistry': False, 'filterMolecularSalts': False, 'requiresLithium': False, 'excludedElements': [], 'flaggedElements': [], 'maxHydrogenAtomicFraction': 1, 'diversifyBy': 'formula', 'maxPerFormula': 1, 'maxPerFamily': 0}`
- pluginPackageVersion: 0.1.0

## Notes

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/notes/2026-05-03T07-32-18-485Z-live-materials-project-high-k-dielectric-oxide-screening-process.md

## Artifacts

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/plots/high-k-dielectric-ranking/candidate-ranking.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/plots/high-k-dielectric-ranking/candidate-ranking.csv
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/plots/high-k-dielectric-ranking/candidate-ranking.jsonl
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1143/mp-1143.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1143/mp-1143.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1143/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-733790/mp-733790.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-733790/mp-733790.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-733790/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-2652/mp-2652.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-2652/mp-2652.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-2652/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1968/mp-1968.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1968/mp-1968.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1968/structure-metrics.png

## Limitations

- Ranking depends on the chosen criteria and available data.
- Offline/mock mode should not be treated as equivalent to live database validation.
- Domain-specific properties such as ion mobility, defect chemistry, electrochemical windows, and interface reactivity require additional calculations or experiments.

