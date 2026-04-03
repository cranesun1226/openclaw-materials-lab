import type { OpenClawCommandProgramLike } from "openclaw/plugin-sdk/plugin-entry";

import { formatErrorForTool } from "../core/errors.js";
import { assertWritableDirectory } from "../core/paths.js";
import type { MaterialsPluginContext } from "../core/runtime-context.js";
import type { MaterialsLabPluginConfig } from "../types/config.js";
import { defaultProcessRunner, type ProcessRunner } from "./process-runner.js";

export interface DoctorOptions {
  json?: boolean;
  pythonPath?: string;
  workspaceRoot?: string;
  cacheDir?: string;
}

export interface DoctorCheck {
  id: string;
  status: "ok" | "warn" | "error";
  message: string;
  details?: unknown;
}

export interface DoctorReport {
  resolvedConfig: Omit<MaterialsLabPluginConfig, "mpApiKey"> & { hasMpApiKey: boolean };
  checks: DoctorCheck[];
}

export function registerDoctorCommand(program: OpenClawCommandProgramLike, context: MaterialsPluginContext): void {
  program
    .command("doctor")
    .description("Check plugin config, Python availability, worker health, writable directories, and API key presence.")
    .option("--json", "Print JSON output")
    .option("--python-path <path>", "Override pythonPath for this invocation")
    .option("--workspace-root <path>", "Override workspaceRoot for this invocation")
    .option("--cache-dir <path>", "Override cacheDir for this invocation")
    .action(async (options: unknown) => {
      const report = await runDoctor(context, normalizeDoctorOptions(options));
      console.log(normalizeDoctorOptions(options).json ? JSON.stringify(report, null, 2) : formatDoctorReport(report));
    });
}

export async function runDoctor(
  context: MaterialsPluginContext,
  options: DoctorOptions = {},
  processRunner: ProcessRunner = defaultProcessRunner,
): Promise<DoctorReport> {
  const overrides = resolveOverrides(options);
  const config = context.resolveConfig(overrides);
  const paths = context.resolvePaths(overrides);
  const checks: DoctorCheck[] = [];

  const versionProbe = await safeCheck(async () => {
    const result = await processRunner(config.pythonPath, ["--version"]);
    if (result.code !== 0) {
      throw new Error((result.stderr || result.stdout || "Unknown Python probe error.").trim());
    }
    return result;
  });
  if (versionProbe.ok) {
    checks.push({
      id: "python-available",
      status: "ok",
      message: `Python executable responded: ${(versionProbe.value.stdout || versionProbe.value.stderr).trim()}`,
    });
  } else {
    checks.push({
      id: "python-available",
      status: "error",
      message: `Python executable check failed: ${formatErrorForTool(versionProbe.error)}`,
    });
  }

  const workspaceCheck = await safeCheck(async () => {
    await context.getArtifactService(overrides).ensureReady();
    await Promise.all([
      assertWritableDirectory(paths.workspaceRoot),
      assertWritableDirectory(paths.cacheDir),
      assertWritableDirectory(paths.notesDir),
      assertWritableDirectory(paths.reportsDir),
      assertWritableDirectory(paths.plotsDir),
      assertWritableDirectory(paths.structuresDir),
    ]);
  });

  checks.push({
    id: "workspace-writable",
    status: workspaceCheck.ok ? "ok" : "error",
    message: workspaceCheck.ok
      ? `Workspace directories are writable under ${paths.workspaceRoot}.`
      : formatErrorForTool(workspaceCheck.error),
  });

  const workerCheck = await safeCheck(async () => context.getBridge(overrides).ping());
  checks.push({
    id: "worker-health",
    status: workerCheck.ok ? "ok" : "error",
    message: workerCheck.ok ? workerCheck.value.summary : formatErrorForTool(workerCheck.error),
  });

  checks.push({
    id: "mp-api-key",
    status: config.mpApiKey ? "ok" : "warn",
    message: config.mpApiKey
      ? "Materials Project API key is configured."
      : "Materials Project API key is not configured. Offline/mock mode is still available.",
  });

  return {
    resolvedConfig: {
      pythonPath: config.pythonPath,
      workspaceRoot: paths.workspaceRoot,
      cacheDir: paths.cacheDir,
      defaultBatchLimit: config.defaultBatchLimit,
      enableAseTools: config.enableAseTools,
      hasMpApiKey: Boolean(config.mpApiKey),
    },
    checks,
  };
}

export function formatDoctorReport(report: DoctorReport): string {
  const lines = [
    "Materials Lab Doctor",
    `pythonPath: ${report.resolvedConfig.pythonPath}`,
    `workspaceRoot: ${report.resolvedConfig.workspaceRoot}`,
    `cacheDir: ${report.resolvedConfig.cacheDir}`,
    `defaultBatchLimit: ${report.resolvedConfig.defaultBatchLimit}`,
    `enableAseTools: ${report.resolvedConfig.enableAseTools}`,
    `hasMpApiKey: ${report.resolvedConfig.hasMpApiKey}`,
    "",
    ...report.checks.map((check) => `[${check.status.toUpperCase()}] ${check.id}: ${check.message}`),
  ];

  return `${lines.join("\n")}\n`;
}

function normalizeDoctorOptions(options: unknown): DoctorOptions {
  const record = (options ?? {}) as Record<string, unknown>;
  const normalized: DoctorOptions = {
    json: Boolean(record.json),
  };

  if (typeof record.pythonPath === "string") {
    normalized.pythonPath = record.pythonPath;
  }

  if (typeof record.workspaceRoot === "string") {
    normalized.workspaceRoot = record.workspaceRoot;
  }

  if (typeof record.cacheDir === "string") {
    normalized.cacheDir = record.cacheDir;
  }

  return normalized;
}

function resolveOverrides(options: DoctorOptions): Partial<MaterialsLabPluginConfig> | undefined {
  const overrides: Partial<MaterialsLabPluginConfig> = {};

  if (options.pythonPath) {
    overrides.pythonPath = options.pythonPath;
  }

  if (options.workspaceRoot) {
    overrides.workspaceRoot = options.workspaceRoot;
  }

  if (options.cacheDir) {
    overrides.cacheDir = options.cacheDir;
  }

  return Object.keys(overrides).length > 0 ? overrides : undefined;
}

async function safeCheck<T>(check: () => Promise<T>): Promise<{ ok: true; value: T } | { ok: false; error: unknown }> {
  try {
    return { ok: true, value: await check() };
  } catch (error) {
    return { ok: false, error };
  }
}
