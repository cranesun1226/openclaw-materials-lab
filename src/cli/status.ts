import type { OpenClawCommandProgramLike } from "openclaw/plugin-sdk/plugin-entry";

import type { MaterialsPluginContext } from "../core/runtime-context.js";
import type { MaterialsLabPluginConfig } from "../types/config.js";

export interface StatusOptions {
  json?: boolean;
  workspaceRoot?: string;
  pythonPath?: string;
}

export interface StatusReport {
  config: Omit<MaterialsLabPluginConfig, "mpApiKey"> & { hasMpApiKey: boolean };
  paths: ReturnType<MaterialsPluginContext["resolvePaths"]>;
  tools: Record<string, string>;
}

export function registerStatusCommand(program: OpenClawCommandProgramLike, context: MaterialsPluginContext): void {
  program
    .command("status")
    .description("Show effective plugin config, resolved directories, and tool availability.")
    .option("--json", "Print JSON output")
    .option("--workspace-root <path>", "Override workspaceRoot for this invocation")
    .option("--python-path <path>", "Override pythonPath for this invocation")
    .action((options: unknown) => {
      const normalized = normalizeStatusOptions(options);
      const report = runStatus(context, normalized);
      console.log(normalized.json ? JSON.stringify(report, null, 2) : formatStatusReport(report));
    });
}

export function runStatus(context: MaterialsPluginContext, options: StatusOptions = {}): StatusReport {
  const overrides = resolveOverrides(options);
  const config = context.resolveConfig(overrides);
  const paths = context.resolvePaths(overrides);
  const allowList = context.loadConfigSource()?.tools?.allow ?? [];

  return {
    config: {
      pythonPath: config.pythonPath,
      workspaceRoot: config.workspaceRoot,
      cacheDir: config.cacheDir,
      defaultBatchLimit: config.defaultBatchLimit,
      enableAseTools: config.enableAseTools,
      hasMpApiKey: Boolean(config.mpApiKey),
    },
    paths,
    tools: {
      materials_search_mp: "required",
      materials_fetch_structure: "required",
      materials_analyze_structure: "required",
      materials_compare_candidates: "required",
      materials_save_note: "required",
      materials_export_report: "required",
      materials_ase_relax: config.enableAseTools
        ? allowList.includes("materials_ase_relax") || allowList.includes("materials-lab")
          ? "optional + enabled + approval-gated"
          : "optional + disabled until added to tools.allow + approval-gated"
        : "disabled by plugin config",
      materials_batch_screen:
        allowList.includes("materials_batch_screen") || allowList.includes("materials-lab")
          ? "optional + enabled + approval-gated"
          : "optional + disabled until added to tools.allow + approval-gated",
    },
  };
}

export function formatStatusReport(report: StatusReport): string {
  const toolLines = Object.entries(report.tools).map(([tool, status]) => `${tool}: ${status}`);
  const pathLines = Object.entries(report.paths).map(([name, value]) => `${name}: ${value}`);

  return `${[
    "Materials Lab Status",
    `pythonPath: ${report.config.pythonPath}`,
    `workspaceRoot: ${report.config.workspaceRoot}`,
    `cacheDir: ${report.config.cacheDir}`,
    `defaultBatchLimit: ${report.config.defaultBatchLimit}`,
    `enableAseTools: ${report.config.enableAseTools}`,
    `hasMpApiKey: ${report.config.hasMpApiKey}`,
    "",
    ...pathLines,
    "",
    ...toolLines,
  ].join("\n")}\n`;
}

function normalizeStatusOptions(options: unknown): StatusOptions {
  const record = (options ?? {}) as Record<string, unknown>;
  const normalized: StatusOptions = {
    json: Boolean(record.json),
  };

  if (typeof record.workspaceRoot === "string") {
    normalized.workspaceRoot = record.workspaceRoot;
  }

  if (typeof record.pythonPath === "string") {
    normalized.pythonPath = record.pythonPath;
  }

  return normalized;
}

function resolveOverrides(options: StatusOptions): Partial<MaterialsLabPluginConfig> | undefined {
  const overrides: Partial<MaterialsLabPluginConfig> = {};

  if (options.workspaceRoot) {
    overrides.workspaceRoot = options.workspaceRoot;
  }

  if (options.pythonPath) {
    overrides.pythonPath = options.pythonPath;
  }

  return Object.keys(overrides).length > 0 ? overrides : undefined;
}
