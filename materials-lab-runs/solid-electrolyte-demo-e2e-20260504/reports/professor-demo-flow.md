# Professor Demo Flow: Solid-State Lithium Electrolyte Screening

Generated for the 2026-05-04 KST demo run.

## Demo Thesis

OpenClaw Materials Lab can take a materials-research goal, query live Materials Project data, build a diverse proxy shortlist, fetch crystal structures, compute lightweight structure descriptors, and export evidence-tracked reports without claiming research-grade discovery.

Recommended one-sentence framing:

> I will demonstrate a lithium solid-state electrolyte screening workflow: from live database search to ranked candidates, structure analysis, evidence limitations, and next-step calculation planning.

## Recommended Live Chat Interaction

Use this as the visible OpenClaw chat prompt:

```text
Find stable lithium solid-state electrolyte candidates from Materials Project.
Use live data only, compare diverse oxide/sulfide/halide families, fetch representative structures,
analyze Li sublattice proxy descriptors, and export an evidence-tracked report.
```

Expected tool sequence to narrate:

1. `materials_search_mp` across solid-electrolyte families.
2. `materials_compare_candidates` with the `solid-electrolyte` preset.
3. `materials_fetch_structure` for family-balanced representative candidates.
4. `materials_analyze_structure` for pymatgen-based structure metrics and Li proxy descriptors.
5. `materials_save_note` to persist the process note.
6. `materials_export_report` to write the final markdown report.

Important narration:

- This is a `proxy-screen`, not a conductivity claim.
- Live Materials Project data is required; offline fallback is disabled.
- Ranking uses stability, minimum band-gap screen, chemistry risk filters, and diversity controls.
- Ionic conductivity, migration barriers, electrochemical window, and interface stability remain missing evidence.

## Terminal E2E Actually Run

These commands were used to verify the system outside the chat UI.

```bash
openclaw --help
openclaw materials status
openclaw materials doctor
npm run build
openclaw plugins list
```

The direct live E2E command was:

```bash
MPLCONFIGDIR=/private/tmp/materials-lab-mpl \
MATERIALS_LAB_RUN_ROOT=/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504 \
node materials-lab-runs/solid-electrolyte-live-e2e-v2-20260503/live-openclaw-e2e-runner.mjs
```

Why `MPLCONFIGDIR` is set:

- The sandbox could not write to `/Users/haksunlee/.matplotlib`.
- Redirecting Matplotlib cache to `/private/tmp` avoids a noisy warning and keeps plot generation stable.

Why `MATERIALS_LAB_RUN_ROOT` is set:

- The original E2E runner had a fixed historical output directory.
- This keeps the professor demo artifacts in a fresh run folder without overwriting the 2026-05-03 validation run.

## Runtime Notes

The first E2E attempt failed because sandboxed DNS could not resolve `api.materialsproject.org`.
The command was re-run with network access enabled, and the live Materials Project E2E completed successfully.

`openclaw materials doctor` showed:

- Python executable responded: Python 3.14.3.
- Materials Lab worker responded: `Materials Lab worker 0.1.0 is ready.`
- Materials Project API key is configured.
- Workspace writability under `~/.openclaw/materials-lab` was blocked by the Codex sandbox, so the demo E2E used a repo-local run directory instead.

## Actual E2E Results

Run root:

```text
/Users/haksunlee/gitpublish/openclaw-materials-lab/materials-lab-runs/solid-electrolyte-demo-e2e-20260504
```

Validation summary:

| Check | Result |
| --- | --- |
| Offline fallback used | `false` |
| Search families | 8 |
| Unique live candidates | 66 |
| Ranked candidates after diversity controls | 12 |
| Ranked max formula multiplicity | 1 |
| Ranked families | garnet-oxide, halide, lgps-like-sulfide, nasicon-oxide, thiophosphate-sulfide, zirconium-phosphate |
| Structures analyzed | 4 |
| Structures with Li proxy metrics | 4 |
| Chemistry-risk exclusions | 18 |
| Required artifacts | 18 checked, 0 missing |

Top ranked candidates:

| Rank | Material | Formula | Family | Score | Band gap eV | eHull eV |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| 1 | mp-556886 | Li4Al3Ge3ClO12 | halide | 0.957174 | 4.1175 | 0.000452765 |
| 2 | mp-554203 | Li4Ga3Si3ClO12 | halide | 0.955432 | 4.5903 | 0 |
| 3 | mp-567652 | Cs2LiYCl6 | halide | 0.953584 | 4.8986 | 0 |
| 4 | mp-11175 | LiZnPS4 | thiophosphate-sulfide | 0.953327 | 2.7312 | 0 |
| 5 | mp-985583 | Li3PS4 | thiophosphate-sulfide | 0.952957 | 2.8091 | 0 |
| 7 | mp-942733 | Li7La3Zr2O12 | garnet-oxide | 0.941598 | 4.1688 | 0.00684601 |

Family-balanced structure analysis candidates:

| Material | Formula | Family |
| --- | --- | --- |
| mp-556886 | Li4Al3Ge3ClO12 | halide |
| mp-11175 | LiZnPS4 | thiophosphate-sulfide |
| mp-942733 | Li7La3Zr2O12 | garnet-oxide |
| mp-766132 | Li2ZrFe(PO4)3 | zirconium-phosphate |

## Artifacts To Show

Primary reports:

- `reports/live-openclaw-solid-electrolyte-e2e-v2-process.md`
- `reports/live-solid-electrolyte-e2e-v2-report.md`
- `reports/live-solid-electrolyte-e2e-v2-summary.json`
- `notes/2026-05-03T23-57-09-574Z-live-materials-project-solid-state-electrolyte-screening-v2-proc.md`

Visual artifacts:

- `plots/solid-electrolyte-ranking-v2/candidate-ranking.png` - 1600 x 880.
- `plots/solid-electrolyte-ranking-v2/domain-evidence.png` - 1600 x 832.
- `structures/mp-556886/structure-metrics.png` - 1440 x 2016.
- `structures/mp-11175/structure-metrics.png` - 1440 x 2016.
- `structures/mp-942733/structure-metrics.png` - 1440 x 2016.
- `structures/mp-766132/structure-metrics.png` - 1440 x 2016.

Data artifacts:

- `plots/solid-electrolyte-ranking-v2/candidate-ranking.csv`
- `plots/solid-electrolyte-ranking-v2/candidate-ranking.jsonl`
- Per-candidate `structure.json` and `.cif` files under `structures/`.

## Suggested 7-Minute Presentation Script

1. Start with the research question.
   "We want a first-pass shortlist of lithium solid-state electrolyte candidates, but we do not want the system to overclaim conductivity."

2. Show OpenClaw configuration health.
   "The plugin is enabled, Python worker is reachable, and the Materials Project key is configured."

3. Run or describe the live search.
   "The workflow searches eight chemistry families: garnet oxides, thiophosphate sulfides, LGPS-like sulfides, NASICON-like oxides, zirconium phosphates, chloride sulfides, chloride halides, and oxyhalides."

4. Show ranking table.
   "The system found 66 unique live candidates and reduced them to 12 diverse ranked candidates. Formula diversity prevents one repeated formula family from dominating the table."

5. Explain one or two candidates.
   "For example, `mp-942733` is LLZO-like garnet oxide, while `mp-985583` is Li3PS4. The list includes multiple plausible families rather than one narrow cluster."

6. Show structure artifacts.
   "The workflow fetched CIF/JSON structures and computed lightweight structural descriptors, including Li proxy metrics. These descriptors are useful triage, not direct ionic conductivity."

7. Show the claim boundary.
   "The report explicitly marks missing evidence: ionic conductivity, migration barrier, electrochemical window, and interface stability. The next step is NEB/BVSE/AIMD or electrochemical-window calculations."

8. Close with reproducibility.
   "Everything is saved as markdown, JSON, CSV, JSONL, CIF, and PNG under a single run directory, so the result can be audited and re-used."

## Screenshot Note

No GUI screenshot was captured in this run. Instead, the workflow generated reusable PNG artifacts that can be dropped directly into slides. If a live screenshot is needed, open the generated markdown report and PNG plots side by side during the presentation.
