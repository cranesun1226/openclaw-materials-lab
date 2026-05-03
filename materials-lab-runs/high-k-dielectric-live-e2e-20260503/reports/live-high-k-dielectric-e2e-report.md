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
| 1 | [mp-1143](https://materialsproject.org/materials/mp-1143) | Al2O3 | binary-oxide | 0 | 5.8537 | 0.919836 | 0.899824 | 0 | duplicate-formula, warning |
| 2 | [mp-733790](https://materialsproject.org/materials/mp-733790) | SiO2 | binary-oxide | 0.0065735 | 5.5868 | 0.883781 | 0.860432 | 0 | duplicate-formula, warning |
| 3 | [mp-2652](https://materialsproject.org/materials/mp-2652) | Y2O3 | binary-oxide | 0 | 4.0973 | 0.874082 | 0.881027 | 0 | duplicate-formula, warning |
| 4 | [mp-1968](https://materialsproject.org/materials/mp-1968) | La2O3 | binary-oxide | 0 | 3.8248 | 0.863706 | 0.878118 | 0 | duplicate-formula, warning |
| 5 | [mp-2858](https://materialsproject.org/materials/mp-2858) | ZrO2 | binary-oxide | 0 | 3.5322 | 0.852756 | 0.875243 | 0 | duplicate-formula, warning |
| 6 | [mp-352](https://materialsproject.org/materials/mp-352) | HfO2 | binary-oxide | 0 | 4.0165 | 0.784976 | 0.767707 | 0 | duplicate-formula, warning |
| 7 | [mp-5020](https://materialsproject.org/materials/mp-5020) | BaTiO3 | perovskite-oxide | 4.099e-05 | 2.5087 | 0.781628 | 0.809492 | 0 | duplicate-formula, warning |
| 8 | [mp-1439](https://materialsproject.org/materials/mp-1439) | TiO2 | binary-oxide | 0.0045236 | 2.5281 | 0.733767 | 0.771466 | 0 | duplicate-formula, warning |
| 9 | [mp-1238961](https://materialsproject.org/materials/mp-1238961) | Ta2O5 | binary-oxide | 0.0139272 | 2.341 | 0.703502 | 0.765216 | 0 | duplicate-formula, warning |

## Ranked Candidates

### 1. [mp-1143](https://materialsproject.org/materials/mp-1143) (Al2O3)

- Score: 0.919836
- Primary score: 0.921114
- Secondary score: 0.899824
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: R-3c
- eHull: 0 eV
- Band gap: 5.8537 eV
- Density: 3.8735 g/cm3
- Duplicate group: Al2O3 (10 candidate(s))
- Risk flags: -
- Weighted stability: 0.423
- Weighted bandGap: 0.35182
- Weighted density: 0.091027
- Weighted secondary: 0.053989
- stability score 1.000
- band-gap alignment 0.936 (target 5.5 eV)
- density alignment 0.646 (target 6.0 g/cm3)
- secondary tie-breaker 0.900 (domain descriptor 1.000, family prior 0.950, gap margin 0.936)
- Warning: Duplicate reduced-formula group appears 10 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.

### 2. [mp-733790](https://materialsproject.org/materials/mp-733790) (SiO2)

- Score: 0.883781
- Primary score: 0.885272
- Secondary score: 0.860432
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: P1
- eHull: 0.0065735 eV
- Band gap: 5.5868 eV
- Density: 2.255 g/cm3
- Duplicate group: SiO2 (12 candidate(s))
- Risk flags: -
- Weighted stability: 0.409097
- Weighted bandGap: 0.370066
- Weighted density: 0.052992
- Weighted secondary: 0.051626
- stability score 0.967
- band-gap alignment 0.984 (target 5.5 eV)
- density alignment 0.376 (target 6.0 g/cm3)
- secondary tie-breaker 0.860 (domain descriptor 1.000, family prior 0.950, gap margin 0.984)
- Warning: Duplicate reduced-formula group appears 12 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.

### 3. [mp-2652](https://materialsproject.org/materials/mp-2652) (Y2O3)

- Score: 0.874082
- Primary score: 0.873639
- Secondary score: 0.881027
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: Ia-3
- eHull: 0 eV
- Band gap: 4.0973 eV
- Density: 5.02612 g/cm3
- Duplicate group: Y2O3 (6 candidate(s))
- Risk flags: -
- Weighted stability: 0.423
- Weighted bandGap: 0.280106
- Weighted density: 0.118114
- Weighted secondary: 0.052862
- stability score 1.000
- band-gap alignment 0.745 (target 5.5 eV)
- density alignment 0.838 (target 6.0 g/cm3)
- secondary tie-breaker 0.881 (domain descriptor 1.000, family prior 0.950, gap margin 0.745)
- Warning: Duplicate reduced-formula group appears 6 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.

### 4. [mp-1968](https://materialsproject.org/materials/mp-1968) (La2O3)

- Score: 0.863706
- Primary score: 0.862787
- Secondary score: 0.878118
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: P-3m1
- eHull: 0 eV
- Band gap: 3.8248 eV
- Density: 6.61523 g/cm3
- Duplicate group: La2O3 (3 candidate(s))
- Risk flags: -
- Weighted stability: 0.423
- Weighted bandGap: 0.261477
- Weighted density: 0.126542
- Weighted secondary: 0.052687
- stability score 1.000
- band-gap alignment 0.695 (target 5.5 eV)
- density alignment 0.897 (target 6.0 g/cm3)
- secondary tie-breaker 0.878 (domain descriptor 1.000, family prior 0.950, gap margin 0.695)
- Warning: Duplicate reduced-formula group appears 3 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.

### 5. [mp-2858](https://materialsproject.org/materials/mp-2858) (ZrO2)

- Score: 0.852756
- Primary score: 0.851321
- Secondary score: 0.875243
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: P2_1/c
- eHull: 0 eV
- Band gap: 3.5322 eV
- Density: 5.77733 g/cm3
- Duplicate group: ZrO2 (12 candidate(s))
- Risk flags: -
- Weighted stability: 0.423
- Weighted bandGap: 0.241474
- Weighted density: 0.135767
- Weighted secondary: 0.052515
- stability score 1.000
- band-gap alignment 0.642 (target 5.5 eV)
- density alignment 0.963 (target 6.0 g/cm3)
- secondary tie-breaker 0.875 (domain descriptor 1.000, family prior 0.950, gap margin 0.642)
- Warning: Duplicate reduced-formula group appears 12 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.

### 6. [mp-352](https://materialsproject.org/materials/mp-352) (HfO2)

- Score: 0.784976
- Primary score: 0.786078
- Secondary score: 0.767707
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: P2_1/c
- eHull: 0 eV
- Band gap: 4.0165 eV
- Density: 10.2412 g/cm3
- Duplicate group: HfO2 (7 candidate(s))
- Risk flags: -
- Weighted stability: 0.423
- Weighted bandGap: 0.274583
- Weighted density: 0.041331
- Weighted secondary: 0.046062
- stability score 1.000
- band-gap alignment 0.730 (target 5.5 eV)
- density alignment 0.293 (target 6.0 g/cm3)
- secondary tie-breaker 0.768 (domain descriptor 1.000, family prior 0.950, gap margin 0.730)
- Warning: Duplicate reduced-formula group appears 7 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.

### 7. [mp-5020](https://materialsproject.org/materials/mp-5020) (BaTiO3)

- Score: 0.781628
- Primary score: 0.779849
- Secondary score: 0.809492
- Risk penalty: 0
- Source: materials-project
- Family: perovskite-oxide
- Space group: R3m
- eHull: 4.099e-05 eV
- Band gap: 2.5087 eV
- Density: 5.89961 g/cm3
- Duplicate group: BaTiO3 (3 candidate(s))
- Risk flags: -
- Weighted stability: 0.422913
- Weighted bandGap: 0.171504
- Weighted density: 0.138641
- Weighted secondary: 0.04857
- stability score 1.000
- band-gap alignment 0.456 (target 5.5 eV)
- density alignment 0.983 (target 6.0 g/cm3)
- secondary tie-breaker 0.809 (domain descriptor 1.000, family prior 0.880, gap margin 0.456)
- Warning: Duplicate reduced-formula group appears 3 times.
- Warning: Material family 'perovskite-oxide' appears 3 times in the candidate pool.

### 8. [mp-1439](https://materialsproject.org/materials/mp-1439) (TiO2)

- Score: 0.733767
- Primary score: 0.731361
- Secondary score: 0.771466
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: Pbcn
- eHull: 0.0045236 eV
- Band gap: 2.5281 eV
- Density: 4.30708 g/cm3
- Duplicate group: TiO2 (12 candidate(s))
- Risk flags: -
- Weighted stability: 0.413433
- Weighted bandGap: 0.17283
- Weighted density: 0.101216
- Weighted secondary: 0.046288
- stability score 0.977
- band-gap alignment 0.460 (target 5.5 eV)
- density alignment 0.718 (target 6.0 g/cm3)
- secondary tie-breaker 0.771 (domain descriptor 1.000, family prior 0.950, gap margin 0.460)
- Warning: Duplicate reduced-formula group appears 12 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.

### 9. [mp-1238961](https://materialsproject.org/materials/mp-1238961) (Ta2O5)

- Score: 0.703502
- Primary score: 0.699562
- Secondary score: 0.765216
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: P2/m
- eHull: 0.0139272 eV
- Band gap: 2.341 eV
- Density: 7.57424 g/cm3
- Duplicate group: Ta2O5 (7 candidate(s))
- Risk flags: -
- Weighted stability: 0.393544
- Weighted bandGap: 0.160039
- Weighted density: 0.104005
- Weighted secondary: 0.045913
- stability score 0.930
- band-gap alignment 0.426 (target 5.5 eV)
- density alignment 0.738 (target 6.0 g/cm3)
- secondary tie-breaker 0.765 (domain descriptor 1.000, family prior 0.950, gap margin 0.426)
- Warning: Duplicate reduced-formula group appears 7 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.

## Why Candidates Might Fail

| Rank | Material | Main Failure Risks |
| ---: | --- | --- |
| 1 | [mp-1143](https://materialsproject.org/materials/mp-1143) | Duplicate reduced-formula group appears 10 times.; Material family 'binary-oxide' appears 69 times in the candidate pool. |
| 2 | [mp-733790](https://materialsproject.org/materials/mp-733790) | Duplicate reduced-formula group appears 12 times.; Material family 'binary-oxide' appears 69 times in the candidate pool. |
| 3 | [mp-2652](https://materialsproject.org/materials/mp-2652) | Duplicate reduced-formula group appears 6 times.; Material family 'binary-oxide' appears 69 times in the candidate pool. |
| 4 | [mp-1968](https://materialsproject.org/materials/mp-1968) | Duplicate reduced-formula group appears 3 times.; Material family 'binary-oxide' appears 69 times in the candidate pool. |
| 5 | [mp-2858](https://materialsproject.org/materials/mp-2858) | Duplicate reduced-formula group appears 12 times.; Material family 'binary-oxide' appears 69 times in the candidate pool. |
| 6 | [mp-352](https://materialsproject.org/materials/mp-352) | Duplicate reduced-formula group appears 7 times.; Material family 'binary-oxide' appears 69 times in the candidate pool. |
| 7 | [mp-5020](https://materialsproject.org/materials/mp-5020) | Duplicate reduced-formula group appears 3 times.; Material family 'perovskite-oxide' appears 3 times in the candidate pool. |
| 8 | [mp-1439](https://materialsproject.org/materials/mp-1439) | Duplicate reduced-formula group appears 12 times.; Material family 'binary-oxide' appears 69 times in the candidate pool. |
| 9 | [mp-1238961](https://materialsproject.org/materials/mp-1238961) | Duplicate reduced-formula group appears 7 times.; Material family 'binary-oxide' appears 69 times in the candidate pool. |

## Method Notes

- This E2E intentionally uses a non-Li, non-battery topic to test whether the plugin generalizes beyond solid electrolytes.
- Ranking is based on generic Materials Project summary fields and should be treated as a triage view only.

## Provenance

- runRoot: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503
- generatedAt: 2026-05-03T07:45:29.381Z
- dataSource: Materials Project live API
- offlineFallbackAllowed: False
- compareCriteria: `{'preset': 'high-k-dielectric', 'screeningLevel': 'proxy-screen', 'stabilityWeight': 0.45, 'bandGapWeight': 0.4, 'densityWeight': 0.15, 'bandGapScoringMode': 'target', 'minimumBandGapEv': 2, 'bandGapTargetEv': 5.5, 'densityScoringMode': 'target', 'densityTargetGcm3': 6, 'secondaryWeight': 0.06, 'riskPenaltyWeight': 0.2, 'preferredBandGapEv': 5.5, 'preferredLiFractionMin': 0, 'preferredLiFractionMax': 1, 'excludeToxicElements': True, 'excludeRiskyChemistry': True, 'filterMolecularSalts': False, 'requiresLithium': False, 'excludedElements': ['Cd', 'Hg', 'Pb', 'Tl', 'Th', 'U'], 'flaggedElements': ['As', 'Be', 'Cr', 'Sb', 'Se'], 'maxHydrogenAtomicFraction': 0.05, 'diversifyBy': 'formula', 'maxPerFormula': 1, 'maxPerFamily': 8}`
- pluginPackageVersion: 0.1.0

## Notes

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/notes/2026-05-03T07-45-29-380Z-live-materials-project-high-k-dielectric-oxide-screening-process.md

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

