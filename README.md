# `@cranesun/openclaw-materials-lab`

Native OpenClaw plugin for evidence-tracked, approval-gated materials-science research workflows. It lets an OpenClaw user describe a research goal in chat and then search candidate materials, fetch structures, analyze them locally, compare options, plan backend-adapter follow-up calculations, save research notes, and export a report. Optional heavier workflows such as ASE-based relaxation, research-plan execution, and batch screening are included behind approval gates.

## Who This Is For

This plugin is for OpenClaw users who already have the gateway running and want a local, inspectable workflow for materials research. It assumes:

- OpenClaw is installed and working.
- You are comfortable configuring a local Python 3.10+ environment.
- You want live Materials Project access for research data, with explicit development fixtures only for smoke testing.

## What The Plugin Does

The plugin provides:

- Native OpenClaw tools for materials search, structure fetch, structure analysis, candidate comparison, dynamic research-protocol compilation, approval-gated execution, note saving, and report export.
- Optional approval-gated tools for ASE relaxation and batch screening.
- A bundled research skill under `skills/material-science-research`.
- A local Python worker under `python/` using stdin/stdout JSON requests.
- CLI commands for setup and diagnostics:
  - `openclaw materials doctor`
  - `openclaw materials setup-python`
  - `openclaw materials status`

## Architecture Overview

The architecture is intentionally thin and explicit:

- `index.ts`: plugin registration only.
- `src/core`: config, paths, protocol, logging, error types, runtime composition.
- `src/services`: Python bridge, artifact management, note persistence.
- `src/tools`: one module per tool.
- `src/cli`: setup and diagnostics commands.
- `src/hooks`: approval behavior for expensive tools.
- `python/materials_lab`: worker, Materials Project adapter, pymatgen operations, ASE operations, report helpers.

The Node side never exposes an HTTP server. The plugin launches a short-lived Python subprocess for each worker request. That keeps v1 simple, debuggable, and easy to package.

## Install

### From npm

```bash
openclaw plugins install @cranesun/openclaw-materials-lab
openclaw gateway restart
```

### From a local path

```bash
npm install
npm run build
openclaw plugins install -l /absolute/path/to/openclaw-materials-lab
openclaw gateway restart
```

If `openclaw plugins list` shows `materials-lab` as disabled after install, run:

```bash
openclaw plugins enable materials-lab
```

## OpenClaw Config Example

Add or update the plugin entry in `~/.openclaw/openclaw.json`:

```json
{
  "plugins": {
    "entries": {
      "materials-lab": {
        "enabled": true,
        "config": {
          "pythonPath": "python3.12",
          "mpApiKey": "mp-your-key-here",
          "workspaceRoot": "~/.openclaw/materials-lab",
          "cacheDir": "~/.openclaw/materials-lab/cache",
          "defaultBatchLimit": 20,
          "enableAseTools": false
        }
      }
    }
  },
  "tools": {
    "allow": [
      "materials_ase_relax",
      "materials_batch_screen",
      "materials_execute_research_plan"
    ]
  }
}
```

`materials_ase_relax`, `materials_batch_screen`, and `materials_execute_research_plan` are registered as optional tools. Users can opt in explicitly through `tools.allow`.

## Python Setup Flow

OpenClaw ignores npm lifecycle hooks during plugin installation, so Python setup is explicit by design.

1. Install or link the plugin.
2. Run:

```bash
openclaw materials setup-python
```

3. Confirm health:

```bash
openclaw materials doctor
openclaw materials status
```

The default setup command creates a virtual environment at `<workspaceRoot>/.venv` and installs `python/requirements.txt`.

### Manual Python Setup

```bash
python3.12 -m venv ~/.openclaw/materials-lab/.venv
~/.openclaw/materials-lab/.venv/bin/pip install -r python/requirements.txt
```

Then point plugin config at the interpreter:

```json
{
  "plugins": {
    "entries": {
      "materials-lab": {
        "config": {
          "pythonPath": "~/.openclaw/materials-lab/.venv/bin/python"
        }
      }
    }
  }
}
```

## Materials Project API Key Setup

Set the key in plugin config or with an environment variable:

- Preferred: `plugins.entries.materials-lab.config.mpApiKey`
- Fallback: `MATERIALS_PROJECT_API_KEY`

Live Materials Project search and structure fetch require a valid key and the `mp-api` Python package. Development fixture data exists only for explicit smoke tests; runtime tools do not fall back to it unless `allowOffline: true` is passed intentionally.

## Example Chat Prompts

- "Find oxide candidates for a stable wide-band-gap dielectric and compare the top five."
- "Search lithium phosphate cathode materials, fetch the top structures, and summarize the most promising candidates."
- "Analyze the structure of `mp-149`, explain the coordination environment at a high level, and save a note."
- "Export a markdown report comparing these three materials for thermal stability and insulating behavior."
- "Compile a research protocol for a lead-free moisture-stable photovoltaic absorber campaign before candidates are known."
- "Given only this research goal, autonomously compile the protocol, search candidate databases, write a candidate pool, and create an evidence ledger before making any claim."
- "Use the ranked candidates to compile an evidence schema and validation queue with a 12-calculation budget."
- "Evaluate whether this candidate's evidence ledger satisfies the claim policy for a research-grade candidate claim."
- "Ingest these Quantum ESPRESSO/VASP outputs into the evidence ledger and re-evaluate the claim gate."
- "Import this literature or experiment CSV/JSON evidence table into the ledger."
- "Execute that research-loop plan with the dev-smoke backend to validate plumbing without generating research property evidence."
- "Prepare Quantum ESPRESSO inputs for the top two calculations in that research-loop plan."
- "Prepare VASP, atomate2/jobflow, or AiiDA backend inputs for this approved plan without submitting jobs."
- "Prepare a batch screening plan, but ask me before running expensive relaxation jobs."

## Workspace Layout

All plugin outputs stay under `workspaceRoot`:

- `notes/`
- `reports/`
- `plots/`
- `structures/`
- `cache/`

The plugin validates paths before writing and rejects attempts to escape the configured workspace.

## Troubleshooting

### `openclaw materials doctor` shows Python worker errors

- Confirm `pythonPath` points to a real interpreter.
- Confirm `pythonPath` points to Python 3.10 or newer.
- Re-run `openclaw materials setup-python`.
- If you use a custom environment, install `python/requirements.txt` into that interpreter.

### Materials Project queries fail

- Confirm `mpApiKey` is set correctly.
- Verify outbound network access from the Python environment.
- For local plumbing tests, pass `allowOffline: true` explicitly to use development fixture data. Do not treat fixture data as research evidence.

### ASE tools do not appear

- Enable `enableAseTools` in plugin config.
- Add the optional tools to `tools.allow`.
- Remember that expensive tools also require runtime approval before execution.

### Files are not written where expected

- Check `workspaceRoot` and `cacheDir` with `openclaw materials status`.
- The plugin never writes outside the validated workspace root.

## Security Notes

- The plugin only launches a configured Python executable and communicates over stdin/stdout JSON.
- There is no shell passthrough or arbitrary command execution surface in tool handlers.
- File writes are restricted to `workspaceRoot`.
- Expensive or write-heavy workflows request approval before execution.
- `materials_plan_research_loop` writes a plan and manifest only. It marks DFT/HPC/paid-compute work as blocked until a human explicitly approves a later execution workflow.
- With only `researchGoal`, `materials_plan_research_loop` now runs the bounded autonomous discovery compiler: it writes a query log, candidate-pool JSONL, evidence-ledger JSONL, and candidate-backed protocol when database candidates are found.
- Autonomous discovery never upgrades a candidate beyond `candidate-hypothesis`/proxy status; research-grade claims remain blocked until the evidence schema is closed with parsed evidence artifacts.
- `materials_evaluate_research_claim` reads a plan plus evidence ledger or imported evidence rows and emits a claim-review certificate. It only allows `research-grade-candidate` when every required evidence gate has traceable, strong evidence and no blocking/conflicting rows.
- `materials_ingest_evidence` parses QE/VASP outputs plus literature/experiment JSON, JSONL, or CSV evidence tables into standard evidence-ledger rows for claim evaluation.
- `materials_execute_research_plan` supports a non-evidentiary `dev-smoke` backend plus prepare/submit adapters for `quantum-espresso`, `vasp`, `atomate2`, and `aiida`.
- External backend adapters default to `executionMode: "prepare"` and write reproducible input decks, structure files, and run/submit scaffolds. They only launch commands when `executionMode: "submit"` and `allowExecution: true` are both provided.
- The `dev-smoke` backend validates execution/provenance plumbing only. It does not emit property updates or reranking payloads.
- External prepared jobs do not produce property-backed candidate updates until completed outputs are parsed back into `propertyUpdates`.
- `mpApiKey` is marked sensitive in plugin UI hints and is also supported through environment variables.

## Development Workflow

```bash
npm install
npm run typecheck
npm test
npm run build
npm run pack:verify
```

Key development notes:

- Tests can opt into development fixture data explicitly.
- The bridge smoke test uses the local Python worker and development fixtures; live Materials Project access is still required for research-grade data retrieval.
- The OpenClaw SDK entrypoint is shimmed at test runtime, but TypeScript resolves against the installed OpenClaw SDK.

## Roadmap

Likely follow-up work after v1:

- broader database connectors beyond Materials Project and better query synthesis,
- ingestion/parsing of completed backend outputs into the evidence ledger,
- literature connector integration with citation-level claim extraction,
- execution adapters for DFPT, NEB, AIMD, optical absorption, defect, and transport workflows,
- more robust pymatgen structural descriptors and plotting,
- resumable batch workflows,
- richer report templating,
- optional long-lived Python worker mode,
- stronger live integration tests behind explicit opt-in flags.
