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

| Rank | Material | Formula | Family | eHull eV | Gap eV | Score | Evidence | Tier | Risk | Flags |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| 1 | [mp-556886](https://materialsproject.org/materials/mp-556886) | Li4Al3Ge3ClO12 | halide | 0.000452765 | 4.1175 | 0.957174 | 0.626855 | watchlist | 0 | warning |
| 2 | [mp-554203](https://materialsproject.org/materials/mp-554203) | Li4Ga3Si3ClO12 | halide | 0 | 4.5903 | 0.955432 | 0.627217 | watchlist | 0 | warning |
| 3 | [mp-567652](https://materialsproject.org/materials/mp-567652) | Cs2LiYCl6 | halide | 0 | 4.8986 | 0.953584 | 0.628 | watchlist | 0 | warning |
| 4 | [mp-11175](https://materialsproject.org/materials/mp-11175) | LiZnPS4 | thiophosphate-sulfide | 0 | 2.7312 | 0.953327 | 0.642571 | watchlist | 0 | warning |
| 5 | [mp-985583](https://materialsproject.org/materials/mp-985583) | Li3PS4 | thiophosphate-sulfide | 0 | 2.8091 | 0.952957 | 0.634 | watchlist | 0 | duplicate-formula, warning |
| 6 | [mp-950995](https://materialsproject.org/materials/mp-950995) | Li6PS5I | thiophosphate-sulfide | 0.00212493 | 2.5333 | 0.943026 | 0.614864 | watchlist | 0 | duplicate-formula, warning |
| 7 | [mp-942733](https://materialsproject.org/materials/mp-942733) | Li7La3Zr2O12 | garnet-oxide | 0.00684601 | 4.1688 | 0.941598 | 0.619523 | watchlist | 0 | warning |
| 8 | [mp-766132](https://materialsproject.org/materials/mp-766132) | Li2ZrFe(PO4)3 | zirconium-phosphate | 0.00301738 | 2.4566 | 0.939509 | 0.636007 | watchlist | 0 | warning |
| 9 | [mp-10499](https://materialsproject.org/materials/mp-10499) | LiZr2(PO4)3 | zirconium-phosphate | 0 | 4.2533 | 0.936461 | 0.579778 | watchlist | 0 | duplicate-formula, warning |
| 10 | [mp-1223569](https://materialsproject.org/materials/mp-1223569) | Li4Zr8V3(P3O16)3 | zirconium-phosphate | 0.00637703 | 3.1339 | 0.915541 | 0.574677 | watchlist | 0 | warning |
| 11 | [mp-696138](https://materialsproject.org/materials/mp-696138) | Li10Ge(PS6)2 | lgps-like-sulfide | 0.0187605 | 2.5395 | 0.903754 | 0.616592 | watchlist | 0 | duplicate-formula, warning |
| 12 | [mp-769074](https://materialsproject.org/materials/mp-769074) | Na2LiTi3Al(PO4)6 | nasicon-oxide | 0.0128596 | 2.5293 | 0.885852 | 0.527712 | watchlist | 0 | duplicate-formula, warning |

## Domain Evidence Matrix

| Rank | Material | Evidence Tier | Source Level | Passing Gates | Missing Properties | Main Next Step |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | [mp-556886](https://materialsproject.org/materials/mp-556886) | watchlist | proxy-only | 3/7 | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | NEB or bond-valence migration barrier for mobile Li pathways |
| 2 | [mp-554203](https://materialsproject.org/materials/mp-554203) | watchlist | proxy-only | 3/7 | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | NEB or bond-valence migration barrier for mobile Li pathways |
| 3 | [mp-567652](https://materialsproject.org/materials/mp-567652) | watchlist | proxy-only | 3/7 | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | NEB or bond-valence migration barrier for mobile Li pathways |
| 4 | [mp-11175](https://materialsproject.org/materials/mp-11175) | watchlist | proxy-only | 3/7 | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | NEB or bond-valence migration barrier for mobile Li pathways |
| 5 | [mp-985583](https://materialsproject.org/materials/mp-985583) | watchlist | proxy-only | 3/7 | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | NEB or bond-valence migration barrier for mobile Li pathways |
| 6 | [mp-950995](https://materialsproject.org/materials/mp-950995) | watchlist | proxy-only | 3/7 | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | NEB or bond-valence migration barrier for mobile Li pathways |
| 7 | [mp-942733](https://materialsproject.org/materials/mp-942733) | watchlist | proxy-only | 3/7 | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | NEB or bond-valence migration barrier for mobile Li pathways |
| 8 | [mp-766132](https://materialsproject.org/materials/mp-766132) | watchlist | proxy-only | 3/7 | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | NEB or bond-valence migration barrier for mobile Li pathways |
| 9 | [mp-10499](https://materialsproject.org/materials/mp-10499) | watchlist | proxy-only | 2/7 | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | NEB or bond-valence migration barrier for mobile Li pathways |
| 10 | [mp-1223569](https://materialsproject.org/materials/mp-1223569) | watchlist | proxy-only | 2/7 | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | NEB or bond-valence migration barrier for mobile Li pathways |
| 11 | [mp-696138](https://materialsproject.org/materials/mp-696138) | watchlist | proxy-only | 3/7 | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | NEB or bond-valence migration barrier for mobile Li pathways |
| 12 | [mp-769074](https://materialsproject.org/materials/mp-769074) | watchlist | proxy-only | 2/7 | ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability | NEB or bond-valence migration barrier for mobile Li pathways |

## Ranked Candidates

### 1. [mp-556886](https://materialsproject.org/materials/mp-556886) (Li4Al3Ge3ClO12)

- Score: 0.957174
- Primary score: 0.998529
- Secondary score: 0.956656
- Domain evidence: 0.626855 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: halide
- Space group: P-43n
- eHull: 0.000452765 eV
- Band gap: 4.1175 eV
- Density: 2.77709 g/cm3
- Duplicate group: Li4Al3Ge3ClO12 (1 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability
- Next calculations: NEB or bond-valence migration barrier for mobile Li pathways; AIMD ionic conductivity at target temperature; grand-potential electrochemical window and electrode interface reactions
- Weighted stability: 0.518823
- Weighted bandGap: 0.28
- Weighted density: 0
- Weighted secondary: 0.095666
- Weighted domainEvidence: 0.062686
- stability score 0.998
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.926 (not weighted)
- secondary tie-breaker 0.957 (domain descriptor 1.000, family prior 0.880, gap margin 0.971)
- research evidence 0.627 (watchlist, proxy-only)
- Warning: Material family 'halide' appears 8 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability.

### 2. [mp-554203](https://materialsproject.org/materials/mp-554203) (Li4Ga3Si3ClO12)

- Score: 0.955432
- Primary score: 1
- Secondary score: 0.927106
- Domain evidence: 0.627217 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: halide
- Space group: P-43n
- eHull: 0 eV
- Band gap: 4.5903 eV
- Density: 2.84933 g/cm3
- Duplicate group: Li4Ga3Si3ClO12 (1 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability
- Next calculations: NEB or bond-valence migration barrier for mobile Li pathways; AIMD ionic conductivity at target temperature; grand-potential electrochemical window and electrode interface reactions
- Weighted stability: 0.52
- Weighted bandGap: 0.28
- Weighted density: 0
- Weighted secondary: 0.092711
- Weighted domainEvidence: 0.062722
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.950 (not weighted)
- secondary tie-breaker 0.927 (domain descriptor 1.000, family prior 0.880, gap margin 0.852)
- research evidence 0.627 (watchlist, proxy-only)
- Warning: Material family 'halide' appears 8 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability.

### 3. [mp-567652](https://materialsproject.org/materials/mp-567652) (Cs2LiYCl6)

- Score: 0.953584
- Primary score: 1
- Secondary score: 0.907837
- Domain evidence: 0.628 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: halide
- Space group: Fm-3m
- eHull: 0 eV
- Band gap: 4.8986 eV
- Density: 3.17828 g/cm3
- Duplicate group: Cs2LiYCl6 (1 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability
- Next calculations: NEB or bond-valence migration barrier for mobile Li pathways; AIMD ionic conductivity at target temperature; grand-potential electrochemical window and electrode interface reactions
- Weighted stability: 0.52
- Weighted bandGap: 0.28
- Weighted density: 0
- Weighted secondary: 0.090784
- Weighted domainEvidence: 0.0628
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.941 (not weighted)
- secondary tie-breaker 0.908 (domain descriptor 1.000, family prior 0.880, gap margin 0.775)
- research evidence 0.628 (watchlist, proxy-only)
- Warning: Material family 'halide' appears 8 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability.

### 4. [mp-11175](https://materialsproject.org/materials/mp-11175) (LiZnPS4)

- Score: 0.953327
- Primary score: 1
- Secondary score: 0.8907
- Domain evidence: 0.642571 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: thiophosphate-sulfide
- Space group: I-4
- eHull: 0 eV
- Band gap: 2.7312 eV
- Density: 2.49727 g/cm3
- Duplicate group: LiZnPS4 (1 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability
- Next calculations: NEB or bond-valence migration barrier for mobile Li pathways; AIMD ionic conductivity at target temperature; grand-potential electrochemical window and electrode interface reactions
- Weighted stability: 0.52
- Weighted bandGap: 0.28
- Weighted density: 0
- Weighted secondary: 0.08907
- Weighted domainEvidence: 0.064257
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.832 (not weighted)
- secondary tie-breaker 0.891 (domain descriptor 1.000, family prior 0.900, gap margin 0.683)
- research evidence 0.643 (watchlist, proxy-only)
- Warning: Material family 'thiophosphate-sulfide' appears 22 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability.

### 5. [mp-985583](https://materialsproject.org/materials/mp-985583) (Li3PS4)

- Score: 0.952957
- Primary score: 1
- Secondary score: 0.895569
- Domain evidence: 0.634 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: thiophosphate-sulfide
- Space group: Pnma
- eHull: 0 eV
- Band gap: 2.8091 eV
- Density: 1.85427 g/cm3
- Duplicate group: Li3PS4 (3 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability
- Next calculations: NEB or bond-valence migration barrier for mobile Li pathways; AIMD ionic conductivity at target temperature; grand-potential electrochemical window and electrode interface reactions
- Weighted stability: 0.52
- Weighted bandGap: 0.28
- Weighted density: 0
- Weighted secondary: 0.089557
- Weighted domainEvidence: 0.0634
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.618 (not weighted)
- secondary tie-breaker 0.896 (domain descriptor 1.000, family prior 0.900, gap margin 0.702)
- research evidence 0.634 (watchlist, proxy-only)
- Warning: Duplicate reduced-formula group appears 3 times.
- Warning: Material family 'thiophosphate-sulfide' appears 22 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability.

### 6. [mp-950995](https://materialsproject.org/materials/mp-950995) (Li6PS5I)

- Score: 0.943026
- Primary score: 0.993094
- Secondary score: 0.870639
- Domain evidence: 0.614864 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: thiophosphate-sulfide
- Space group: Cc
- eHull: 0.00212493 eV
- Band gap: 2.5333 eV
- Density: 2.221 g/cm3
- Duplicate group: Li6PS5I (2 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability
- Next calculations: NEB or bond-valence migration barrier for mobile Li pathways; AIMD ionic conductivity at target temperature; grand-potential electrochemical window and electrode interface reactions
- Weighted stability: 0.514475
- Weighted bandGap: 0.28
- Weighted density: 0
- Weighted secondary: 0.087064
- Weighted domainEvidence: 0.061486
- stability score 0.989
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.740 (not weighted)
- secondary tie-breaker 0.871 (domain descriptor 0.974, family prior 0.900, gap margin 0.633)
- research evidence 0.615 (watchlist, proxy-only)
- Warning: Duplicate reduced-formula group appears 2 times.
- Warning: Material family 'thiophosphate-sulfide' appears 22 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability.

### 7. [mp-942733](https://materialsproject.org/materials/mp-942733) (Li7La3Zr2O12)

- Score: 0.941598
- Primary score: 0.97775
- Secondary score: 0.97445
- Domain evidence: 0.619523 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: garnet-oxide
- Space group: I4_1/acd
- eHull: 0.00684601 eV
- Band gap: 4.1688 eV
- Density: 5.0131 g/cm3
- Duplicate group: Li7La3Zr2O12 (1 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability
- Next calculations: NEB or bond-valence migration barrier for mobile Li pathways; AIMD ionic conductivity at target temperature; grand-potential electrochemical window and electrode interface reactions
- Weighted stability: 0.5022
- Weighted bandGap: 0.28
- Weighted density: 0
- Weighted secondary: 0.097445
- Weighted domainEvidence: 0.061952
- stability score 0.966
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.329 (not weighted)
- secondary tie-breaker 0.974 (domain descriptor 1.000, family prior 0.950, gap margin 0.958)
- research evidence 0.620 (watchlist, proxy-only)
- Warning: Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability.

### 8. [mp-766132](https://materialsproject.org/materials/mp-766132) (Li2ZrFe(PO4)3)

- Score: 0.939509
- Primary score: 0.990194
- Secondary score: 0.837537
- Domain evidence: 0.636007 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: zirconium-phosphate
- Space group: Pna2_1
- eHull: 0.00301738 eV
- Band gap: 2.4566 eV
- Density: 3.04392 g/cm3
- Duplicate group: Li2ZrFe(PO4)3 (1 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability
- Next calculations: NEB or bond-valence migration barrier for mobile Li pathways; AIMD ionic conductivity at target temperature; grand-potential electrochemical window and electrode interface reactions
- Weighted stability: 0.512155
- Weighted bandGap: 0.28
- Weighted density: 0
- Weighted secondary: 0.083754
- Weighted domainEvidence: 0.063601
- stability score 0.985
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.985 (not weighted)
- secondary tie-breaker 0.838 (domain descriptor 1.000, family prior 0.780, gap margin 0.614)
- research evidence 0.636 (watchlist, proxy-only)
- Warning: Material family 'zirconium-phosphate' appears 11 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability.

### 9. [mp-10499](https://materialsproject.org/materials/mp-10499) (LiZr2(PO4)3)

- Score: 0.936461
- Primary score: 1
- Secondary score: 0.784837
- Domain evidence: 0.579778 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: zirconium-phosphate
- Space group: P2_1/c
- eHull: 0 eV
- Band gap: 4.2533 eV
- Density: 3.2197 g/cm3
- Duplicate group: LiZr2(PO4)3 (6 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability
- Next calculations: NEB or bond-valence migration barrier for mobile Li pathways; AIMD ionic conductivity at target temperature; grand-potential electrochemical window and electrode interface reactions
- Weighted stability: 0.52
- Weighted bandGap: 0.28
- Weighted density: 0
- Weighted secondary: 0.078484
- Weighted domainEvidence: 0.057978
- stability score 1.000
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.927 (not weighted)
- secondary tie-breaker 0.785 (domain descriptor 0.556, family prior 0.780, gap margin 0.937)
- research evidence 0.580 (watchlist, proxy-only)
- Warning: Duplicate reduced-formula group appears 6 times.
- Warning: Material family 'zirconium-phosphate' appears 11 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability.

### 10. [mp-1223569](https://materialsproject.org/materials/mp-1223569) (Li4Zr8V3(P3O16)3)

- Score: 0.915541
- Primary score: 0.979275
- Secondary score: 0.746537
- Domain evidence: 0.574677 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: zirconium-phosphate
- Space group: P1
- eHull: 0.00637703 eV
- Band gap: 3.1339 eV
- Density: 3.05728 g/cm3
- Duplicate group: Li4Zr8V3(P3O16)3 (1 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability
- Next calculations: NEB or bond-valence migration barrier for mobile Li pathways; AIMD ionic conductivity at target temperature; grand-potential electrochemical window and electrode interface reactions
- Weighted stability: 0.50342
- Weighted bandGap: 0.28
- Weighted density: 0
- Weighted secondary: 0.074654
- Weighted domainEvidence: 0.057468
- stability score 0.968
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.981 (not weighted)
- secondary tie-breaker 0.747 (domain descriptor 0.556, family prior 0.780, gap margin 0.783)
- research evidence 0.575 (watchlist, proxy-only)
- Warning: Material family 'zirconium-phosphate' appears 11 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability.

### 11. [mp-696138](https://materialsproject.org/materials/mp-696138) (Li10Ge(PS6)2)

- Score: 0.903754
- Primary score: 0.939028
- Secondary score: 0.908719
- Domain evidence: 0.616592 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: lgps-like-sulfide
- Space group: P1
- eHull: 0.0187605 eV
- Band gap: 2.5395 eV
- Density: 1.97713 g/cm3
- Duplicate group: Li10Ge(PS6)2 (2 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability
- Next calculations: NEB or bond-valence migration barrier for mobile Li pathways; AIMD ionic conductivity at target temperature; grand-potential electrochemical window and electrode interface reactions
- Weighted stability: 0.471223
- Weighted bandGap: 0.28
- Weighted density: 0
- Weighted secondary: 0.090872
- Weighted domainEvidence: 0.061659
- stability score 0.906
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.659 (not weighted)
- secondary tie-breaker 0.909 (domain descriptor 1.000, family prior 1.000, gap margin 0.635)
- research evidence 0.617 (watchlist, proxy-only)
- Warning: Duplicate reduced-formula group appears 2 times.
- Warning: Material family 'lgps-like-sulfide' appears 2 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability.

### 12. [mp-769074](https://materialsproject.org/materials/mp-769074) (Na2LiTi3Al(PO4)6)

- Score: 0.885852
- Primary score: 0.958206
- Secondary score: 0.665162
- Domain evidence: 0.527712 (watchlist)
- Risk penalty: 0
- Source: materials-project
- Family: nasicon-oxide
- Space group: P1
- eHull: 0.0128596 eV
- Band gap: 2.5293 eV
- Density: 2.83734 g/cm3
- Duplicate group: Na2LiTi3Al(PO4)6 (2 candidate(s))
- Risk flags: -
- Evidence source level: proxy-only
- Missing research properties: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability
- Next calculations: NEB or bond-valence migration barrier for mobile Li pathways; AIMD ionic conductivity at target temperature; grand-potential electrochemical window and electrode interface reactions
- Weighted stability: 0.486565
- Weighted bandGap: 0.28
- Weighted density: 0
- Weighted secondary: 0.066516
- Weighted domainEvidence: 0.052771
- stability score 0.936
- band-gap minimum screen 1.000 (min 2.0 eV)
- density advisory 0.946 (not weighted)
- secondary tie-breaker 0.665 (domain descriptor 0.270, family prior 0.920, gap margin 0.632)
- research evidence 0.528 (watchlist, proxy-only)
- Warning: Duplicate reduced-formula group appears 2 times.
- Warning: Material family 'nasicon-oxide' appears 4 times in the candidate pool.
- Warning: Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability.

## Why Candidates Might Fail

| Rank | Material | Main Failure Risks |
| ---: | --- | --- |
| 1 | [mp-556886](https://materialsproject.org/materials/mp-556886) | missing research evidence: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV; Material family 'halide' appears 8 times in the candidate pool.; Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability. |
| 2 | [mp-554203](https://materialsproject.org/materials/mp-554203) | missing research evidence: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV; Material family 'halide' appears 8 times in the candidate pool.; Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability. |
| 3 | [mp-567652](https://materialsproject.org/materials/mp-567652) | missing research evidence: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV; Material family 'halide' appears 8 times in the candidate pool.; Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability. |
| 4 | [mp-11175](https://materialsproject.org/materials/mp-11175) | missing research evidence: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV; Material family 'thiophosphate-sulfide' appears 22 times in the candidate pool.; Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability. |
| 5 | [mp-985583](https://materialsproject.org/materials/mp-985583) | missing research evidence: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV; Duplicate reduced-formula group appears 3 times.; Material family 'thiophosphate-sulfide' appears 22 times in the candidate pool.; Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability. |
| 6 | [mp-950995](https://materialsproject.org/materials/mp-950995) | missing research evidence: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV; Duplicate reduced-formula group appears 2 times.; Material family 'thiophosphate-sulfide' appears 22 times in the candidate pool.; Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability. |
| 7 | [mp-942733](https://materialsproject.org/materials/mp-942733) | missing research evidence: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV; Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability. |
| 8 | [mp-766132](https://materialsproject.org/materials/mp-766132) | missing research evidence: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV; Material family 'zirconium-phosphate' appears 11 times in the candidate pool.; Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability. |
| 9 | [mp-10499](https://materialsproject.org/materials/mp-10499) | missing research evidence: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV; Duplicate reduced-formula group appears 6 times.; Material family 'zirconium-phosphate' appears 11 times in the candidate pool.; Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability. |
| 10 | [mp-1223569](https://materialsproject.org/materials/mp-1223569) | missing research evidence: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV; Material family 'zirconium-phosphate' appears 11 times in the candidate pool.; Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability. |
| 11 | [mp-696138](https://materialsproject.org/materials/mp-696138) | missing research evidence: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV; Duplicate reduced-formula group appears 2 times.; Material family 'lgps-like-sulfide' appears 2 times in the candidate pool.; Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability. |
| 12 | [mp-769074](https://materialsproject.org/materials/mp-769074) | missing research evidence: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV; Duplicate reduced-formula group appears 2 times.; Material family 'nasicon-oxide' appears 4 times in the candidate pool.; Research evidence is incomplete; missing: ionicConductivityScm, migrationBarrierEv, electrochemicalWindowV, interfaceStability. |

## Method Notes

- Compared against the earlier E2E weakness where one formula family dominated the top ranks.
- Formula diversity was enabled to force a shortlist of distinct hypotheses.
- Family-balanced structure selection was enabled to avoid analyzing only the first ranked family.
- CSV and JSONL ranking artifacts were required for downstream researcher review.

## Provenance

- runRoot: /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504
- generatedAt: 2026-05-03T23:57:09.576Z
- dataSource: Materials Project live API
- offlineFallbackAllowed: False
- compareCriteria: `{'preset': 'solid-electrolyte', 'screeningLevel': 'proxy-screen', 'stabilityWeight': 0.65, 'bandGapWeight': 0.35, 'densityWeight': 0, 'bandGapScoringMode': 'minimum', 'minimumBandGapEv': 2, 'bandGapTargetEv': 5, 'densityScoringMode': 'advisory', 'densityTargetGcm3': 3, 'secondaryWeight': 0.1, 'evidenceWeight': 0.1, 'riskPenaltyWeight': 0.3, 'preferredBandGapEv': 4, 'preferredLiFractionMin': 0.1, 'preferredLiFractionMax': 0.45, 'excludeToxicElements': True, 'excludeRiskyChemistry': True, 'filterMolecularSalts': True, 'requiresLithium': True, 'excludedElements': ['Be', 'Cd', 'Hg', 'Pb', 'Tl', 'Th', 'U'], 'flaggedElements': ['As', 'Cr', 'Sb', 'Se'], 'maxHydrogenAtomicFraction': 0.15, 'diversifyBy': 'formula', 'maxPerFormula': 1, 'maxPerFamily': 3}`
- pluginPackageVersion: 0.1.0

## Notes

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/notes/2026-05-03T23-57-09-574Z-live-materials-project-solid-state-electrolyte-screening-v2-proc.md

## Artifacts

- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/plots/solid-electrolyte-ranking-v2/candidate-ranking.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/plots/solid-electrolyte-ranking-v2/domain-evidence.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/plots/solid-electrolyte-ranking-v2/candidate-ranking.csv
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/plots/solid-electrolyte-ranking-v2/candidate-ranking.jsonl
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/structures/mp-556886/mp-556886.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/structures/mp-556886/mp-556886.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/structures/mp-556886/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/structures/mp-11175/mp-11175.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/structures/mp-11175/mp-11175.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/structures/mp-11175/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/structures/mp-942733/mp-942733.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/structures/mp-942733/mp-942733.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/structures/mp-942733/structure-metrics.png
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/structures/mp-766132/mp-766132.json
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/structures/mp-766132/mp-766132.cif
- /Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504/structures/mp-766132/structure-metrics.png

## Limitations

- Ranking depends on the chosen criteria and available data.
- Development fixture data is for smoke testing only and should not be treated as live database validation.
- Domain-specific properties such as ion mobility, defect chemistry, electrochemical windows, and interface reactivity require additional calculations or experiments.

