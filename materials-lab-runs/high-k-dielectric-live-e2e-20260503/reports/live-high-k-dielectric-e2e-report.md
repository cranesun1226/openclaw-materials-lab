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

| Rank | Material | Formula | Family | eHull eV | Gap eV | Score | Evidence | Tier | Risk | Flags |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| 1 | [mp-1143](https://materialsproject.org/materials/mp-1143) | Al2O3 | binary-oxide | 0 | 5.8537 | 0.891138 | 0.681958 | proxy-shortlist | 0 | duplicate-formula, warning |
| 2 | [mp-2652](https://materialsproject.org/materials/mp-2652) | Y2O3 | binary-oxide | 0 | 4.0973 | 0.856206 | 0.724672 | proxy-shortlist | 0 | duplicate-formula, warning |
| 3 | [mp-733790](https://materialsproject.org/materials/mp-733790) | SiO2 | binary-oxide | 0.0065735 | 5.5868 | 0.856147 | 0.654983 | watchlist | 0 | duplicate-formula, warning |
| 4 | [mp-1968](https://materialsproject.org/materials/mp-1968) | La2O3 | binary-oxide | 0 | 3.8248 | 0.846673 | 0.720839 | proxy-shortlist | 0 | duplicate-formula, warning |
| 5 | [mp-2858](https://materialsproject.org/materials/mp-2858) | ZrO2 | binary-oxide | 0 | 3.5322 | 0.841419 | 0.756848 | proxy-shortlist | 0 | duplicate-formula, warning |
| 6 | [mp-5020](https://materialsproject.org/materials/mp-5020) | BaTiO3 | perovskite-oxide | 4.099e-05 | 2.5087 | 0.775554 | 0.72924 | proxy-shortlist | 0 | duplicate-formula, warning |
| 7 | [mp-352](https://materialsproject.org/materials/mp-352) | HfO2 | binary-oxide | 0 | 4.0165 | 0.775523 | 0.707307 | proxy-shortlist | 0 | duplicate-formula, warning |
| 8 | [mp-1439](https://materialsproject.org/materials/mp-1439) | TiO2 | binary-oxide | 0.0045236 | 2.5281 | 0.724747 | 0.656196 | watchlist | 0 | duplicate-formula, warning |
| 9 | [mp-1238961](https://materialsproject.org/materials/mp-1238961) | Ta2O5 | binary-oxide | 0.0139272 | 2.341 | 0.697727 | 0.651439 | watchlist | 0 | duplicate-formula, warning |

## Domain Evidence Matrix

| Rank | Material | Evidence Tier | Source Level | Passing Gates | Missing Properties | Main Next Step |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | [mp-1143](https://materialsproject.org/materials/mp-1143) | proxy-shortlist | proxy-only | 3/6 | dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv | DFPT dielectric tensor with electronic and ionic components |
| 2 | [mp-2652](https://materialsproject.org/materials/mp-2652) | proxy-shortlist | proxy-only | 4/6 | dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv | DFPT dielectric tensor with electronic and ionic components |
| 3 | [mp-733790](https://materialsproject.org/materials/mp-733790) | watchlist | proxy-only | 3/6 | dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv | DFPT dielectric tensor with electronic and ionic components |
| 4 | [mp-1968](https://materialsproject.org/materials/mp-1968) | proxy-shortlist | proxy-only | 4/6 | dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv | DFPT dielectric tensor with electronic and ionic components |
| 5 | [mp-2858](https://materialsproject.org/materials/mp-2858) | proxy-shortlist | proxy-only | 4/6 | dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv | DFPT dielectric tensor with electronic and ionic components |
| 6 | [mp-5020](https://materialsproject.org/materials/mp-5020) | proxy-shortlist | proxy-only | 3/6 | dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv | DFPT dielectric tensor with electronic and ionic components |
| 7 | [mp-352](https://materialsproject.org/materials/mp-352) | proxy-shortlist | proxy-only | 4/6 | dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv | DFPT dielectric tensor with electronic and ionic components |
| 8 | [mp-1439](https://materialsproject.org/materials/mp-1439) | watchlist | proxy-only | 2/6 | dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv | DFPT dielectric tensor with electronic and ionic components |
| 9 | [mp-1238961](https://materialsproject.org/materials/mp-1238961) | watchlist | proxy-only | 2/6 | dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv | DFPT dielectric tensor with electronic and ionic components |

## Ranked Candidates

### 1. [mp-1143](https://materialsproject.org/materials/mp-1143) (Al2O3)

- Score: 0.891138
- Primary score: 0.921114
- Secondary score: 0.899824
- Domain evidence: 0.681958 (proxy-shortlist)
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: R-3c
- eHull: 0 eV
- Band gap: 5.8537 eV
- Density: 3.8735 g/cm3
- Duplicate group: Al2O3 (10 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv, phononStability
- Next calculations: DFPT dielectric tensor with electronic and ionic components; band alignment against Si or the intended channel material; interface reaction energy and oxygen vacancy formation energy
- Weighted stability: 0.369
- Weighted bandGap: 0.306907
- Weighted density: 0.079407
- Weighted secondary: 0.053989
- Weighted domainEvidence: 0.081835
- stability score 1.000
- band-gap alignment 0.936 (target 5.5 eV)
- density alignment 0.646 (target 6.0 g/cm3)
- secondary tie-breaker 0.900 (domain descriptor 1.000, family prior 0.950, gap margin 0.936)
- research evidence 0.682 (proxy-shortlist, proxy-only)
- Warning: Duplicate reduced-formula group appears 10 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv.

### 2. [mp-2652](https://materialsproject.org/materials/mp-2652) (Y2O3)

- Score: 0.856206
- Primary score: 0.873639
- Secondary score: 0.881027
- Domain evidence: 0.724672 (proxy-shortlist)
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: Ia-3
- eHull: 0 eV
- Band gap: 4.0973 eV
- Density: 5.02612 g/cm3
- Duplicate group: Y2O3 (6 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv, phononStability
- Next calculations: DFPT dielectric tensor with electronic and ionic components; band alignment against Si or the intended channel material; interface reaction energy and oxygen vacancy formation energy
- Weighted stability: 0.369
- Weighted bandGap: 0.244348
- Weighted density: 0.103036
- Weighted secondary: 0.052862
- Weighted domainEvidence: 0.086961
- stability score 1.000
- band-gap alignment 0.745 (target 5.5 eV)
- density alignment 0.838 (target 6.0 g/cm3)
- secondary tie-breaker 0.881 (domain descriptor 1.000, family prior 0.950, gap margin 0.745)
- research evidence 0.725 (proxy-shortlist, proxy-only)
- Warning: Duplicate reduced-formula group appears 6 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv.

### 3. [mp-733790](https://materialsproject.org/materials/mp-733790) (SiO2)

- Score: 0.856147
- Primary score: 0.885272
- Secondary score: 0.860432
- Domain evidence: 0.654983 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: P1
- eHull: 0.0065735 eV
- Band gap: 5.5868 eV
- Density: 2.255 g/cm3
- Duplicate group: SiO2 (12 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv, phononStability
- Next calculations: DFPT dielectric tensor with electronic and ionic components; band alignment against Si or the intended channel material; interface reaction energy and oxygen vacancy formation energy
- Weighted stability: 0.356872
- Weighted bandGap: 0.322824
- Weighted density: 0.046227
- Weighted secondary: 0.051626
- Weighted domainEvidence: 0.078598
- stability score 0.967
- band-gap alignment 0.984 (target 5.5 eV)
- density alignment 0.376 (target 6.0 g/cm3)
- secondary tie-breaker 0.860 (domain descriptor 1.000, family prior 0.950, gap margin 0.984)
- research evidence 0.655 (watchlist, proxy-only)
- Warning: Duplicate reduced-formula group appears 12 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv.

### 4. [mp-1968](https://materialsproject.org/materials/mp-1968) (La2O3)

- Score: 0.846673
- Primary score: 0.862787
- Secondary score: 0.878118
- Domain evidence: 0.720839 (proxy-shortlist)
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: P-3m1
- eHull: 0 eV
- Band gap: 3.8248 eV
- Density: 6.61523 g/cm3
- Duplicate group: La2O3 (3 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv, phononStability
- Next calculations: DFPT dielectric tensor with electronic and ionic components; band alignment against Si or the intended channel material; interface reaction energy and oxygen vacancy formation energy
- Weighted stability: 0.369
- Weighted bandGap: 0.228097
- Weighted density: 0.110388
- Weighted secondary: 0.052687
- Weighted domainEvidence: 0.086501
- stability score 1.000
- band-gap alignment 0.695 (target 5.5 eV)
- density alignment 0.897 (target 6.0 g/cm3)
- secondary tie-breaker 0.878 (domain descriptor 1.000, family prior 0.950, gap margin 0.695)
- research evidence 0.721 (proxy-shortlist, proxy-only)
- Warning: Duplicate reduced-formula group appears 3 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv.

### 5. [mp-2858](https://materialsproject.org/materials/mp-2858) (ZrO2)

- Score: 0.841419
- Primary score: 0.851321
- Secondary score: 0.875243
- Domain evidence: 0.756848 (proxy-shortlist)
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: P2_1/c
- eHull: 0 eV
- Band gap: 3.5322 eV
- Density: 5.77733 g/cm3
- Duplicate group: ZrO2 (12 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv, phononStability
- Next calculations: DFPT dielectric tensor with electronic and ionic components; band alignment against Si or the intended channel material; interface reaction energy and oxygen vacancy formation energy
- Weighted stability: 0.369
- Weighted bandGap: 0.210648
- Weighted density: 0.118435
- Weighted secondary: 0.052515
- Weighted domainEvidence: 0.090822
- stability score 1.000
- band-gap alignment 0.642 (target 5.5 eV)
- density alignment 0.963 (target 6.0 g/cm3)
- secondary tie-breaker 0.875 (domain descriptor 1.000, family prior 0.950, gap margin 0.642)
- research evidence 0.757 (proxy-shortlist, proxy-only)
- Warning: Duplicate reduced-formula group appears 12 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv.

### 6. [mp-5020](https://materialsproject.org/materials/mp-5020) (BaTiO3)

- Score: 0.775554
- Primary score: 0.779849
- Secondary score: 0.809492
- Domain evidence: 0.72924 (proxy-shortlist)
- Risk penalty: 0
- Source: materials-project
- Family: perovskite-oxide
- Space group: R3m
- eHull: 4.099e-05 eV
- Band gap: 2.5087 eV
- Density: 5.89961 g/cm3
- Duplicate group: BaTiO3 (3 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv, phononStability
- Next calculations: DFPT dielectric tensor with electronic and ionic components; band alignment against Si or the intended channel material; interface reaction energy and oxygen vacancy formation energy
- Weighted stability: 0.368924
- Weighted bandGap: 0.14961
- Weighted density: 0.120942
- Weighted secondary: 0.04857
- Weighted domainEvidence: 0.087509
- stability score 1.000
- band-gap alignment 0.456 (target 5.5 eV)
- density alignment 0.983 (target 6.0 g/cm3)
- secondary tie-breaker 0.809 (domain descriptor 1.000, family prior 0.880, gap margin 0.456)
- research evidence 0.729 (proxy-shortlist, proxy-only)
- Warning: Duplicate reduced-formula group appears 3 times.
- Warning: Material family 'perovskite-oxide' appears 3 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv.

### 7. [mp-352](https://materialsproject.org/materials/mp-352) (HfO2)

- Score: 0.775523
- Primary score: 0.786078
- Secondary score: 0.767707
- Domain evidence: 0.707307 (proxy-shortlist)
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: P2_1/c
- eHull: 0 eV
- Band gap: 4.0165 eV
- Density: 10.2412 g/cm3
- Duplicate group: HfO2 (7 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv, phononStability
- Next calculations: DFPT dielectric tensor with electronic and ionic components; band alignment against Si or the intended channel material; interface reaction energy and oxygen vacancy formation energy
- Weighted stability: 0.369
- Weighted bandGap: 0.239529
- Weighted density: 0.036055
- Weighted secondary: 0.046062
- Weighted domainEvidence: 0.084877
- stability score 1.000
- band-gap alignment 0.730 (target 5.5 eV)
- density alignment 0.293 (target 6.0 g/cm3)
- secondary tie-breaker 0.768 (domain descriptor 1.000, family prior 0.950, gap margin 0.730)
- research evidence 0.707 (proxy-shortlist, proxy-only)
- Warning: Duplicate reduced-formula group appears 7 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv.

### 8. [mp-1439](https://materialsproject.org/materials/mp-1439) (TiO2)

- Score: 0.724747
- Primary score: 0.731361
- Secondary score: 0.771466
- Domain evidence: 0.656196 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: Pbcn
- eHull: 0.0045236 eV
- Band gap: 2.5281 eV
- Density: 4.30708 g/cm3
- Duplicate group: TiO2 (12 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv, phononStability
- Next calculations: DFPT dielectric tensor with electronic and ionic components; band alignment against Si or the intended channel material; interface reaction energy and oxygen vacancy formation energy
- Weighted stability: 0.360654
- Weighted bandGap: 0.150767
- Weighted density: 0.088295
- Weighted secondary: 0.046288
- Weighted domainEvidence: 0.078744
- stability score 0.977
- band-gap alignment 0.460 (target 5.5 eV)
- density alignment 0.718 (target 6.0 g/cm3)
- secondary tie-breaker 0.771 (domain descriptor 1.000, family prior 0.950, gap margin 0.460)
- research evidence 0.656 (watchlist, proxy-only)
- Warning: Duplicate reduced-formula group appears 12 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv.

### 9. [mp-1238961](https://materialsproject.org/materials/mp-1238961) (Ta2O5)

- Score: 0.697727
- Primary score: 0.699562
- Secondary score: 0.765216
- Domain evidence: 0.651439 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: binary-oxide
- Space group: P2/m
- eHull: 0.0139272 eV
- Band gap: 2.341 eV
- Density: 7.57424 g/cm3
- Duplicate group: Ta2O5 (7 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv, phononStability
- Next calculations: DFPT dielectric tensor with electronic and ionic components; band alignment against Si or the intended channel material; interface reaction energy and oxygen vacancy formation energy
- Weighted stability: 0.343304
- Weighted bandGap: 0.139609
- Weighted density: 0.090728
- Weighted secondary: 0.045913
- Weighted domainEvidence: 0.078173
- stability score 0.930
- band-gap alignment 0.426 (target 5.5 eV)
- density alignment 0.738 (target 6.0 g/cm3)
- secondary tie-breaker 0.765 (domain descriptor 1.000, family prior 0.950, gap margin 0.426)
- research evidence 0.651 (watchlist, proxy-only)
- Warning: Duplicate reduced-formula group appears 7 times.
- Warning: Material family 'binary-oxide' appears 69 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv.

## Why Candidates Might Fail

| Rank | Material | Main Failure Risks |
| ---: | --- | --- |
| 1 | [mp-1143](https://materialsproject.org/materials/mp-1143) | missing research evidence: dielectricTotal, dielectricElectronic, bandOffsetElectronEv; Duplicate reduced-formula group appears 10 times.; Material family 'binary-oxide' appears 69 times in the candidate pool.; Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv. |
| 2 | [mp-2652](https://materialsproject.org/materials/mp-2652) | missing research evidence: dielectricTotal, dielectricElectronic, bandOffsetElectronEv; Duplicate reduced-formula group appears 6 times.; Material family 'binary-oxide' appears 69 times in the candidate pool.; Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv. |
| 3 | [mp-733790](https://materialsproject.org/materials/mp-733790) | missing research evidence: dielectricTotal, dielectricElectronic, bandOffsetElectronEv; Duplicate reduced-formula group appears 12 times.; Material family 'binary-oxide' appears 69 times in the candidate pool.; Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv. |
| 4 | [mp-1968](https://materialsproject.org/materials/mp-1968) | missing research evidence: dielectricTotal, dielectricElectronic, bandOffsetElectronEv; Duplicate reduced-formula group appears 3 times.; Material family 'binary-oxide' appears 69 times in the candidate pool.; Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv. |
| 5 | [mp-2858](https://materialsproject.org/materials/mp-2858) | missing research evidence: dielectricTotal, dielectricElectronic, bandOffsetElectronEv; Duplicate reduced-formula group appears 12 times.; Material family 'binary-oxide' appears 69 times in the candidate pool.; Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv. |
| 6 | [mp-5020](https://materialsproject.org/materials/mp-5020) | missing research evidence: dielectricTotal, dielectricElectronic, bandOffsetElectronEv; Duplicate reduced-formula group appears 3 times.; Material family 'perovskite-oxide' appears 3 times in the candidate pool.; Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv. |
| 7 | [mp-352](https://materialsproject.org/materials/mp-352) | missing research evidence: dielectricTotal, dielectricElectronic, bandOffsetElectronEv; Duplicate reduced-formula group appears 7 times.; Material family 'binary-oxide' appears 69 times in the candidate pool.; Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv. |
| 8 | [mp-1439](https://materialsproject.org/materials/mp-1439) | missing research evidence: dielectricTotal, dielectricElectronic, bandOffsetElectronEv; Duplicate reduced-formula group appears 12 times.; Material family 'binary-oxide' appears 69 times in the candidate pool.; Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv. |
| 9 | [mp-1238961](https://materialsproject.org/materials/mp-1238961) | missing research evidence: dielectricTotal, dielectricElectronic, bandOffsetElectronEv; Duplicate reduced-formula group appears 7 times.; Material family 'binary-oxide' appears 69 times in the candidate pool.; Research evidence is incomplete; missing: dielectricTotal, dielectricElectronic, bandOffsetElectronEv, bandOffsetHoleEv, interfaceReactionEnergyEv. |

## Method Notes

- This E2E intentionally uses a non-Li, non-battery topic to test whether the plugin generalizes beyond solid electrolytes.
- Ranking is based on generic Materials Project summary fields and should be treated as a triage view only.

## Provenance

- runRoot: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503
- generatedAt: 2026-05-03T08:08:38.321Z
- dataSource: Materials Project live API
- offlineFallbackAllowed: False
- compareCriteria: `{'preset': 'high-k-dielectric', 'screeningLevel': 'proxy-screen', 'stabilityWeight': 0.45, 'bandGapWeight': 0.4, 'densityWeight': 0.15, 'bandGapScoringMode': 'target', 'minimumBandGapEv': 2, 'bandGapTargetEv': 5.5, 'densityScoringMode': 'target', 'densityTargetGcm3': 6, 'secondaryWeight': 0.06, 'evidenceWeight': 0.12, 'riskPenaltyWeight': 0.2, 'preferredBandGapEv': 5.5, 'preferredLiFractionMin': 0, 'preferredLiFractionMax': 1, 'excludeToxicElements': True, 'excludeRiskyChemistry': True, 'filterMolecularSalts': False, 'requiresLithium': False, 'excludedElements': ['Cd', 'Hg', 'Pb', 'Tl', 'Th', 'U'], 'flaggedElements': ['As', 'Be', 'Cr', 'Sb', 'Se'], 'maxHydrogenAtomicFraction': 0.05, 'diversifyBy': 'formula', 'maxPerFormula': 1, 'maxPerFamily': 8}`
- pluginPackageVersion: 0.1.0

## Notes

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/notes/2026-05-03T08-08-38-319Z-live-materials-project-high-k-dielectric-oxide-screening-process.md

## Artifacts

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/plots/high-k-dielectric-ranking/candidate-ranking.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/plots/high-k-dielectric-ranking/domain-evidence.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/plots/high-k-dielectric-ranking/candidate-ranking.csv
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/plots/high-k-dielectric-ranking/candidate-ranking.jsonl
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1143/mp-1143.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1143/mp-1143.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1143/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-2652/mp-2652.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-2652/mp-2652.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-2652/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-733790/mp-733790.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-733790/mp-733790.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-733790/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1968/mp-1968.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1968/mp-1968.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/high-k-dielectric-live-e2e-20260503/structures/mp-1968/structure-metrics.png

## Limitations

- Ranking depends on the chosen criteria and available data.
- Offline/mock mode should not be treated as equivalent to live database validation.
- Domain-specific properties such as ion mobility, defect chemistry, electrochemical windows, and interface reactivity require additional calculations or experiments.

