import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import type { MaterialsPluginContext } from "../core/runtime-context.js";
import type { MaterialsCommandProgramLike } from "../types/cli.js";
import type { MaterialsLabPluginConfig } from "../types/config.js";
import { defaultProcessRunner, type ProcessRunner } from "./process-runner.js";

export interface SetupPythonOptions {
  json?: boolean;
  pythonPath?: string;
  workspaceRoot?: string;
  targetPath?: string;
  skipInstall?: boolean;
}

export interface SetupPythonReport {
  venvPath: string;
  interpreterPath: string;
  requirementsPath: string;
  steps: string[];
}

export function registerSetupPythonCommand(program: MaterialsCommandProgramLike, context: MaterialsPluginContext): void {
  program
    .command("setup-python")
    .description("Create or prepare a local Python environment and install plugin requirements.")
    .option("--json", "Print JSON output")
    .option("--python-path <path>", "Base Python interpreter used to create the environment")
    .option("--workspace-root <path>", "Override workspaceRoot for this invocation")
    .option("--target-path <path>", "Virtualenv destination (default: <workspaceRoot>/.venv)")
    .option("--skip-install", "Create the venv but skip pip installation")
    .action(async (options: unknown) => {
      const normalized = normalizeSetupOptions(options);
      const report = await runSetupPython(context, normalized);
      console.log(normalized.json ? JSON.stringify(report, null, 2) : formatSetupPythonReport(report));
    });
}

export async function runSetupPython(
  context: MaterialsPluginContext,
  options: SetupPythonOptions = {},
  processRunner: ProcessRunner = defaultProcessRunner,
): Promise<SetupPythonReport> {
  const overrides = resolveOverrides(options);
  const config = context.resolveConfig(overrides);
  const paths = context.resolvePaths(overrides);
  const venvPath = path.resolve(options.targetPath ?? path.join(paths.workspaceRoot, ".venv"));
  const basePython = options.pythonPath ?? config.pythonPath;
  const requirementsPath = resolveRequirementsPath(import.meta.url);
  const steps: string[] = [];

  await context.getArtifactService(overrides).ensureReady();

  const createVenv = await processRunner(basePython, ["-m", "venv", venvPath]);
  if (createVenv.code !== 0) {
    throw new Error(`Failed to create virtual environment: ${(createVenv.stderr || createVenv.stdout).trim()}`);
  }
  steps.push(`Created or updated virtualenv at ${venvPath}`);

  const interpreterPath = resolveVenvPythonPath(venvPath);
  if (!options.skipInstall) {
    const install = await processRunner(interpreterPath, ["-m", "pip", "install", "-r", requirementsPath]);
    if (install.code !== 0) {
      throw new Error(`Failed to install Python requirements: ${(install.stderr || install.stdout).trim()}`);
    }

    steps.push(`Installed requirements from ${requirementsPath}`);
  } else {
    steps.push("Skipped pip installation by request.");
  }

  return {
    venvPath,
    interpreterPath,
    requirementsPath,
    steps,
  };
}

export function formatSetupPythonReport(report: SetupPythonReport): string {
  return `${["Materials Lab Python Setup", `venvPath: ${report.venvPath}`, `interpreterPath: ${report.interpreterPath}`, `requirementsPath: ${report.requirementsPath}`, "", ...report.steps.map((step) => `- ${step}`)].join("\n")}\n`;
}

function normalizeSetupOptions(options: unknown): SetupPythonOptions {
  const record = (options ?? {}) as Record<string, unknown>;
  const normalized: SetupPythonOptions = {
    json: Boolean(record.json),
    skipInstall: Boolean(record.skipInstall),
  };

  if (typeof record.pythonPath === "string") {
    normalized.pythonPath = record.pythonPath;
  }

  if (typeof record.workspaceRoot === "string") {
    normalized.workspaceRoot = record.workspaceRoot;
  }

  if (typeof record.targetPath === "string") {
    normalized.targetPath = record.targetPath;
  }

  return normalized;
}

function resolveOverrides(options: SetupPythonOptions): Partial<MaterialsLabPluginConfig> | undefined {
  const overrides: Partial<MaterialsLabPluginConfig> = {};

  if (options.pythonPath) {
    overrides.pythonPath = options.pythonPath;
  }

  if (options.workspaceRoot) {
    overrides.workspaceRoot = options.workspaceRoot;
  }

  return Object.keys(overrides).length > 0 ? overrides : undefined;
}

function resolveRequirementsPath(moduleUrl: string): string {
  const start = path.dirname(fileURLToPath(moduleUrl));
  let current = start;

  while (true) {
    const candidate = path.join(current, "python", "requirements.txt");
    if (existsSync(candidate)) {
      return candidate;
    }

    const parent = path.dirname(current);
    if (parent === current) {
      break;
    }

    current = parent;
  }

  throw new Error("Could not locate python/requirements.txt from the plugin package.");
}

function resolveVenvPythonPath(venvPath: string): string {
  return process.platform === "win32"
    ? path.join(venvPath, "Scripts", "python.exe")
    : path.join(venvPath, "bin", "python");
}
