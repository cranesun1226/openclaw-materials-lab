# Live Solid Electrolyte E2E V2 Validation Review

Reviewed run: `materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503`

Review date: 2026-05-03

## Verdict

The patched E2E succeeded. It used live Materials Project data only, applied the updated `solid-electrolyte` preset, generated the ranking table artifacts, enforced formula diversity, excluded chemistry-risk candidates, broke score saturation with secondary tie-breakers, selected structures in a family-balanced way, and produced Li proxy metrics for fetched structures.

This is a clear improvement over the first solid-electrolyte run, where one formula family dominated the top ranks. The V2 result is still a proxy screen, not a research-grade electrolyte discovery result.

## Validation Checks

| Check | Result |
| --- | --- |
| Live Materials Project only | Pass |
| Offline fallback used | `false` |
| Search families | 8 |
| Unique live candidates | 66 |
| Ranked candidates | 12 |
| Formula diversity max multiplicity | 1 |
| Ranked families | garnet oxide, halide, LGPS-like sulfide, NASICON oxide, thiophosphate sulfide, zirconium phosphate |
| Structures analyzed | 4 |
| Structures with Li proxy metrics | 4 |
| Chemistry-risk exclusions | 18 |
| Family-balanced structure families | garnet oxide, halide, thiophosphate sulfide, zirconium phosphate |
| Required artifacts | 17 checked, 0 missing |
| CSV ranking artifact | Present |
| JSONL ranking artifact | Present |
| Enhanced report confidence block | Present |

## What Improved

- Formula diversity worked: each ranked formula appears once.
- The top list now includes multiple families instead of only `LiZr2(PO4)3`.
- Score saturation was reduced: the top candidates now span roughly `0.994` to `0.929` instead of having the first seven candidates stuck at `1.0`.
- Chemistry-risk filtering removed 18 candidates, including toxic/high-risk and molecular-salt-like compositions.
- Structure fetch is now family-balanced rather than simply taking the first four ranked materials.
- `Li7La3Zr2O12` is no longer heavily penalized by density because density is advisory in the solid-electrolyte preset.
- Ranking artifacts are more useful for downstream review: PNG, CSV, and JSONL are all generated.
- Report output now includes a confidence level, domain warnings, candidate table, Materials Project links, score components, duplicate flags, method notes, and provenance.
- Structure metric plots are unit-aware rather than mixing volume, density, angles, and counts on one axis.
- Structure analysis now records Li proxy descriptors such as Li count, Li number density, Li-Li distance, and a simple connectivity proxy.

## Remaining Issues Found By The E2E

### Score Saturation

The previous V2 run had the first seven ranked candidates at score `1.0`. The new secondary tie-breaker fixed this immediate problem. Scores are now separated by composition-level Li fraction, family prior, band-gap margin, and chemistry risk.

This is still not a true transport score. The secondary score should eventually be replaced or augmented by structure-aware transport evidence:

- Li-site network topology from structures,
- BVSE/BVEL-style pathway descriptors,
- migration barrier estimates or NEB/AIMD workflow generation,
- electrochemical stability and interface reactivity.

### Search Space Still Needs Domain Filters

The updated V2 search now excludes several questionable candidates, including toxic/high-risk and H-rich or molecular-salt-like compositions. This is a strong improvement.

The remaining need is not just filtering, but better domain typing:

- distinguish crystalline ceramic electrolytes from salts, hydrates, and molecular compounds,
- apply family-specific element and prototype expectations,
- keep override knobs for exploratory chemistry.

### Family Classification Is Still Heuristic

Current family labels come from element-set rules. This is useful for a first pass, but it can misclassify edge cases and does not identify prototypes. The next step should use structure matching, space-group/prototype signatures, and known formula families.

### Structure Proxies Are Useful But Not Transport

The top four fetched structures all received sparse or insufficient Li connectivity proxies. That is useful as a warning, but it is not equivalent to ionic conductivity. A research-grade workflow still needs BVSE/BVEL, NEB/AIMD input generation, electrochemical window calculations, or literature-backed benchmark comparisons.

### Plots Are Better, But Still Not Polished

The score component plot is readable and more informative than the first version. The structure plots are unit-aware, but label lengths and whitespace still need refinement. Future plots should include cross-candidate comparison panels and family-level scatter plots.

## Recommended Next Patch

1. Add a `solid-electrolyte-strict` preset.
2. Add prototype/family detection with `SpacegroupAnalyzer` and structure matching.
3. Use structure-derived Li topology as a second-pass reranker after structure fetch.
4. Add electrochemical-window and decomposition-product workflows.
5. Add toxicity/cost/abundance risk tables to the report.
6. Add family-level benchmark controls for LLZO, LGPS, argyrodites, halides, and NASICONs.

## Bottom Line

The E2E validates the patch: the plugin now produces a more transparent, diverse, chemistry-aware proxy shortlist with stronger artifacts. The next research-quality gap is deeper transport and electrochemical evidence, not more generic scalar scoring.
