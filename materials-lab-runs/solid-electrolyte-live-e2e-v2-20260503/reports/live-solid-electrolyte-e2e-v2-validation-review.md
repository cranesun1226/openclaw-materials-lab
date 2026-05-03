# Live Solid Electrolyte E2E V2 Validation Review

Reviewed run: `materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503`

Review date: 2026-05-03

## Verdict

The patched E2E succeeded. It used live Materials Project data only, applied the new `solid-electrolyte` preset, generated the new ranking table artifacts, enforced formula diversity, and produced Li proxy metrics for fetched structures.

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
| Required artifacts | 17 checked, 0 missing |
| CSV ranking artifact | Present |
| JSONL ranking artifact | Present |
| Enhanced report confidence block | Present |

## What Improved

- Formula diversity worked: each ranked formula appears once.
- The top list now includes multiple families instead of only `LiZr2(PO4)3`.
- `Li7La3Zr2O12` is no longer heavily penalized by density because density is advisory in the solid-electrolyte preset.
- Ranking artifacts are more useful for downstream review: PNG, CSV, and JSONL are all generated.
- Report output now includes a confidence level, domain warnings, candidate table, Materials Project links, score components, duplicate flags, method notes, and provenance.
- Structure metric plots are unit-aware rather than mixing volume, density, angles, and counts on one axis.
- Structure analysis now records Li proxy descriptors such as Li count, Li number density, Li-Li distance, and a simple connectivity proxy.

## Remaining Issues Found By The E2E

### Score Saturation

The first seven ranked candidates have score `1.0`. This happens because the solid-electrolyte preset treats band gap as a minimum screen and density as unweighted. Once a material has eHull `0` and band gap above the minimum, the score saturates.

This is scientifically safer than over-penalizing LLZO by density, but it makes top-rank ordering less informative. The next scoring patch should add secondary tie-breakers, such as:

- smaller energy above hull after the primary gate,
- family-balanced interleaving,
- Li number density or Li topology proxy when structures are available,
- exclusion/risk penalties for toxic or chemically unsuitable elements,
- known-family priors or benchmark labels.

### Search Space Still Needs Domain Filters

The V2 search found chemically diverse results, but some are questionable solid-electrolyte candidates. Examples include `LiY(TlCl3)2` because of thallium toxicity and `LiClO4`, which is not a normal inorganic ceramic solid-electrolyte candidate despite matching the element filter.

The plugin needs query-time filters and post-ranking risk flags:

- exclude toxic or high-risk elements by default for battery electrolyte screens,
- separate salts/oxidizers from ceramic or glassy solid-electrolyte families,
- flag H-rich or unusual compositions for manual review,
- support family-specific formula/prototype queries rather than only element-set queries.

### Family Classification Is Still Heuristic

Current family labels come from element-set rules. This is useful for a first pass, but it can misclassify edge cases and does not identify prototypes. The next step should use structure matching, space-group/prototype signatures, and known formula families.

### Structure Proxies Are Useful But Not Transport

The top four fetched structures all received sparse or insufficient Li connectivity proxies. That is useful as a warning, but it is not equivalent to ionic conductivity. A research-grade workflow still needs BVSE/BVEL, NEB/AIMD input generation, electrochemical window calculations, or literature-backed benchmark comparisons.

### Plots Are Better, But Still Not Polished

The score component plot is readable and more informative than the first version. The structure plots are unit-aware, but label lengths and whitespace still need refinement. Future plots should include cross-candidate comparison panels and family-level scatter plots.

## Recommended Next Patch

1. Add a `solid-electrolyte-strict` preset.
2. Keep eHull and band gap as gates, then rank by secondary evidence.
3. Add query/ranking filters for toxic elements and chemically unsuitable salts.
4. Add family-balanced structure fetching: at least one structure per top family.
5. Add prototype/family detection with `SpacegroupAnalyzer` and structure matching.
6. Add a final report section named `Why This Candidate Might Fail`.

## Bottom Line

The E2E validates the patch: the plugin now produces a more transparent and diverse proxy shortlist with stronger artifacts. It also reveals the next important research-quality gap: after basic stability and electronic-insulation gates pass, the workflow needs transport-aware and chemistry-aware tie-breakers.
