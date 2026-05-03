# Research Validity Review and Plugin Roadmap

Reviewed run: `materials-lab-runs/solid-electrolyte-live-e2e-20260503`

Review date: 2026-05-03

## Executive Verdict

This run is a valid technical end-to-end OpenClaw Materials Lab execution: it used live Materials Project data, disabled offline fallback, fetched structures, generated plots, wrote process notes, and produced machine-readable validation metadata.

Scientifically, the output should be treated as a proxy screening smoke test, not as a research-grade solid electrolyte discovery result. The current ranking is transparent and reproducible, but the score is not electrolyte-specific enough to support strong conclusions about Li-ion conductivity, electrochemical compatibility, or experimental promise.

The most important issue is composition and family collapse: 6 of the top 10 ranked candidates are `LiZr2(PO4)3`, and the top 3 are all `LiZr2(PO4)3` polymorphs. That means the workflow currently identifies one scoring-favored chemistry repeatedly instead of producing a diverse shortlist of electrolyte hypotheses.

## Reviewed Artifacts

- Final report: `reports/live-solid-electrolyte-e2e-report.md`
- Process report: `reports/live-openclaw-solid-electrolyte-e2e-process.md`
- Summary JSON: `reports/live-solid-electrolyte-e2e-summary.json`
- Process note: `notes/2026-05-03T06-39-02-325Z-live-materials-project-solid-state-electrolyte-screening-process.md`
- Candidate ranking plot: `plots/solid-electrolyte-ranking/candidate-ranking.png`
- Structure artifacts for `mp-759280`, `mp-10499`, and `mp-773068`

## What Is Technically Sound

- Live Materials Project use is clearly validated. `usedOfflineDataAnywhere` is `false`.
- Five electrolyte-adjacent query families were attempted: garnet, thiophosphate, LGPS-like, NASICON-like, and phosphate.
- The workflow found 27 unique live candidates and ranked 10.
- Three structures were fetched and analyzed without fallback or fetch failure.
- Required artifacts were checked and all 12 expected artifacts existed.
- The runner records enough process detail to reproduce the scoring inputs and artifact locations.

## Ranking Assessment

The current scoring formula uses:

- Stability weight: 0.50
- Band-gap alignment weight: 0.35
- Density alignment weight: 0.15
- Band-gap target: 5.0 eV
- Density target: 3.0 g/cm3

This is reasonable as a generic inorganic-materials proxy, but weak for solid electrolytes. A good solid electrolyte needs high ionic conductivity, low electronic conductivity, compatible electrochemical window, chemical/interface stability, manufacturability, and often favorable dopability or defect chemistry. The current score directly measures none of the ion-transport or electrochemical-window requirements.

### Top Candidate Pattern

| Rank | MP ID | Formula | Space Group | eHull eV | Gap eV | Density g/cm3 | Score |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: |
| 1 | mp-759280 | LiZr2(PO4)3 | P-1 | 0.0081 | 4.4307 | 3.0197 | 0.938947 |
| 2 | mp-10499 | LiZr2(PO4)3 | P2_1/c | 0.0000 | 4.2533 | 3.2197 | 0.936746 |
| 3 | mp-773068 | LiZr2(PO4)3 | Cc | 0.0111 | 4.3114 | 3.0024 | 0.923921 |
| 4 | mp-681439 | LiZr2(PO4)3 | C2 | 0.0159 | 4.2307 | 2.9561 | 0.904112 |
| 5 | mp-541661 | LiZr2(PO4)3 | R-3c | 0.0178 | 4.1404 | 3.2104 | 0.884761 |
| 6 | mp-1223743 | Li2Zr4As3(PO8)3 | Pc | 0.0120 | 3.9866 | 3.3300 | 0.882630 |
| 7 | mp-773074 | LiZr2(PO4)3 | P1 | 0.0313 | 4.3898 | 2.9933 | 0.878595 |
| 8 | mp-1222872 | Li2Zr4As3(PO8)3 | R32 | 0.0203 | 3.7145 | 3.2965 | 0.844328 |
| 9 | mp-942733 | Li7La3Zr2O12 | I4_1/acd | 0.0068 | 4.1688 | 5.0131 | 0.824046 |
| 10 | mp-11175 | LiZnPS4 | I-4 | 0.0000 | 2.7312 | 2.4973 | 0.816047 |

The ranking is internally consistent with the score definition, but the definition biases the result. `Li7La3Zr2O12`, a canonical garnet-type solid electrolyte family, is ranked ninth mainly because the density target is 3.0 g/cm3 and its density alignment is only 0.329. That penalty is not scientifically compelling for garnet solid electrolytes. A dense oxide garnet is not automatically less interesting as a solid electrolyte.

Similarly, sulfide and LGPS-like materials can be under-ranked by a rigid 5.0 eV band-gap target or by family search imbalance. Lower band gap does matter for electronic leakage risk, but it should not be used as a near-standalone proxy for electrolyte quality.

## Plot Assessment

The candidate ranking plot is valid as a visual smoke test: it is readable, non-empty, and ordered. For research use, it needs more information. It should show formula or family labels, score components, raw eHull/band gap/density values, and ideally confidence or warning annotations.

The structure metric plots are not research-grade. They combine different units and scales on one y-axis: number of sites, volume, density, lattice constants, angles, and element count. Volume dominates the axis, making density, lattice constants, and element count visually uninformative. These plots are useful only to confirm that structure parsing worked.

For structure interpretation, the plugin should provide separate unit-aware plots and actual structure views: Li sublattice, candidate diffusion pathways, coordination environments, bottleneck distances, and possibly a 3D viewer or rendered thumbnails from CIF.

## Report Assessment

The generated report is honest about limitations, but too thin for a researcher. The current report says the workflow does not compute Li-ion conductivity, migration barriers, or electrochemical windows, which is good. However, it does not sufficiently prevent overinterpretation.

Missing details:

- A full table of raw candidate properties.
- Query payloads and filters per family.
- Materials Project links and provenance fields.
- Software versions and API/data timestamp.
- Composition/prototype deduplication explanation.
- Family coverage and recall limitations.
- Domain-specific caveats for garnets, sulfides, NASICONs, halides, antiperovskites, and argyrodites.
- A next-step plan separating computational validation from experimental validation.

## What Real Researchers Would Still Need

Researchers would need at least the following before using this output for candidate selection:

- Composition-diverse shortlist rather than many polymorphs of one formula.
- Oxidation-state and charge-balance validation.
- Space group/prototype grouping and polymorph deduplication.
- Li-site topology: Li-Li distances, connected Li network dimensionality, bottleneck sizes, and coordination environments.
- Ionic migration descriptors: BVSE/BVEL-style pathway analysis, graph-based diffusion descriptors, or NEB/AIMD workflow generation.
- Electrochemical stability window against Li metal and relevant cathode chemical potentials.
- Chemical/interface reactivity with electrodes and common coatings.
- Finite-temperature and disorder handling, especially for known conductive phases.
- Dopant/vacancy modeling for families such as LLZO and NASICON.
- Synthesis feasibility, air/moisture stability, cost, toxicity, and elemental supply flags.
- Literature links or at least known-family annotations.

## Plugin Development Roadmap

### P0: Make Current Outputs Harder To Misread

- Add a `screeningLevel` field: `technical-smoke`, `proxy-screen`, `research-shortlist`, or `validated-candidate`.
- Put a domain-specific warning block at the top of reports when ion mobility has not been calculated.
- Export a candidate CSV/JSONL table with all raw fields and score components.
- Add Materials Project web links for each `mp-id`.
- Include exact query payloads, API source, OpenClaw version, plugin version, Python version, pymatgen version, and run timestamp.
- Mark duplicate formulas and repeated prototypes directly in the ranking table.

### P1: Add Solid Electrolyte Domain Logic

- Create a `solid-electrolyte` preset with family-aware search expansion.
- Search more families: LLZO/garnets, NASICON/LATP/LAGP, LGPS, argyrodites, thiophosphates, halides, antiperovskites, oxyhalides, and borohydrides.
- Add formula/prototype/space-group grouping so top-N results are diverse by default.
- Replace density-target scoring with weaker family-conditioned heuristics or remove it from primary ranking.
- Treat band gap as a minimum or risk flag, not a target alignment that penalizes legitimate material classes.
- Add a family-balanced ranking mode, for example top 2 per family before global reranking.

### P2: Add Research-Useful Structure Analysis

- Use pymatgen structure matching and `SpacegroupAnalyzer` for prototype grouping.
- Add oxidation-state assignment and charge-balance checks.
- Compute Li sublattice descriptors: Li count per volume, nearest Li-Li distances, Li coordination, connected Li network dimensionality, and bottleneck estimates.
- Add Voronoi/BVSE/BVEL-inspired migration pathway features where dependencies allow.
- Generate unit-aware plots: score contribution bars, eHull vs band gap scatter, density by family, family/prototype diversity, and separate lattice/angle panels.
- Add CIF-based 3D structure thumbnails or an HTML viewer artifact.

### P3: Move Toward Actionable Candidate Validation

- Add grand-potential phase diagram workflows for electrochemical stability windows.
- Add decomposition products and interface compatibility summaries.
- Generate NEB/AIMD input decks for selected candidates rather than pretending to compute diffusion cheaply.
- Integrate ML potential relaxations and diffusion descriptors when available.
- Add literature-aware annotations and known-family benchmarking.
- Build benchmark E2E tests with known positive controls such as LLZO, LGPS, argyrodites, halides, NASICONs, and known negative controls.

## Recommended Next E2E Experiment

Run the same live Materials Project pipeline again with a stricter research-oriented configuration:

- Deduplicate by reduced formula and structure prototype.
- Cap each formula family to one or two candidates.
- Use stability as a gate, not the dominant ranking feature.
- Use band gap as a minimum electronic-insulation screen.
- Remove density from the primary score or make it family-conditioned.
- Add Li-network descriptors before final ranking.
- Generate a report that separates `proxy score`, `transport evidence`, `electrochemical evidence`, and `known missing evidence`.

This would turn the workflow from "OpenClaw can call Materials Project and rank candidates" into "OpenClaw can produce a defensible research shortlist with visible uncertainty."

## Bottom Line

The run is successful as an OpenClaw E2E validation. It is not yet sufficient as a solid-electrolyte discovery workflow. The plugin's next big step is not more generic ranking; it is domain-aware evidence: diversity control, Li transport descriptors, electrochemical stability, richer provenance, and reports that make the confidence level impossible to misunderstand.
