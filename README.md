# `@cranesun/openclaw-materials-lab`

Native OpenClaw plugin for autonomous materials-science research. It lets an OpenClaw user describe a research goal in chat and then search candidate materials, fetch structures, analyze them locally, compare options, save research notes, and export a report. Optional heavier workflows such as ASE-based relaxation and batch screening are included behind approval gates.

## Who This Is For

This plugin is for OpenClaw users who already have the gateway running and want a local, inspectable workflow for materials research. It assumes:

- OpenClaw is installed and working.
- You are comfortable configuring a local Python environment.
- You may want live Materials Project access, but you still want sensible offline behavior for testing and development.

## What The Plugin Does

The plugin provides:

- Native OpenClaw tools for materials search, structure fetch, structure analysis, candidate comparison, note saving, and report export.
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
openclaw plugins enable materials-lab
```

### From a local path

```bash
npm install
npm run build
openclaw plugins install /absolute/path/to/openclaw-materials-lab
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
          "pythonPath": "python3",
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
      "materials_batch_screen"
    ]
  }
}
```

`materials_ase_relax` and `materials_batch_screen` are registered as optional tools. Users can opt in explicitly through `tools.allow`.

## Python Setup Flow

OpenClaw ignores npm lifecycle hooks during plugin installation, so Python setup is explicit by design.

1. Install the package and enable the plugin.
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
python3 -m venv ~/.openclaw/materials-lab/.venv
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

If no key is present, the plugin still works in offline/mock mode for testing. Live Materials Project search and structure fetch require a valid key and the `mp-api` Python package.

## Example Chat Prompts

- "Find oxide candidates for a stable wide-band-gap dielectric and compare the top five."
- "Search lithium phosphate cathode materials, fetch the top structures, and summarize the most promising candidates."
- "Analyze the structure of `mp-149`, explain the coordination environment at a high level, and save a note."
- "Export a markdown report comparing these three materials for thermal stability and insulating behavior."
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
- Re-run `openclaw materials setup-python`.
- If you use a custom environment, install `python/requirements.txt` into that interpreter.

### Materials Project queries fail

- Confirm `mpApiKey` is set correctly.
- Verify outbound network access from the Python environment.
- Use offline mode or the mock dataset while debugging tool flow locally.

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

- Tests default to offline/mock behavior.
- The bridge test uses the local Python worker and does not require live Materials Project access.
- The OpenClaw SDK entrypoint is shimmed in tests so the plugin can be validated without a full gateway runtime.

## Roadmap

Likely follow-up work after v1:

- richer Materials Project query support and better search ranking,
- more robust pymatgen structural descriptors and plotting,
- resumable batch workflows,
- richer report templating,
- optional long-lived Python worker mode,
- stronger live integration tests behind explicit opt-in flags.
