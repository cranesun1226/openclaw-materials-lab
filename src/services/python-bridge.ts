import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { createBridgeRequest, parseBridgeResponse } from "../core/bridge-protocol.js";
import { ConfigurationError, PythonBridgeError } from "../core/errors.js";
import type { MaterialsLogger } from "../core/logger.js";
import type {
  AnalyzeStructurePayload,
  AnalyzeStructureResult,
  AseRelaxPayload,
  AseRelaxResult,
  BatchScreenPayload,
  BatchScreenResult,
  BridgeAction,
  BridgeSuccess,
  CompareCandidatesPayload,
  CompareCandidatesResult,
  ExportReportPayload,
  ExportReportResult,
  FetchStructurePayload,
  FetchStructureResult,
  SearchMaterialsPayload,
  SearchMaterialsResult,
} from "../types/bridge.js";
import type { MaterialsLabPluginConfig, MaterialsWorkspacePaths } from "../types/config.js";

const DEFAULT_TIMEOUT_MS = 60_000;

export class PythonBridgeService {
  private readonly pluginRoot: string;
  private readonly pythonModuleRoot: string;

  public constructor(
    private readonly config: MaterialsLabPluginConfig,
    private readonly workspacePaths: MaterialsWorkspacePaths,
    private readonly logger: MaterialsLogger,
  ) {
    this.pluginRoot = resolvePluginRoot(import.meta.url);
    this.pythonModuleRoot = path.join(this.pluginRoot, "python");
  }

  public async warmup(): Promise<void> {
    await this.ping();
  }

  public async stop(): Promise<void> {}

  public async ping(): Promise<BridgeSuccess<{ worker: string; python: string }>> {
    return this.call("ping", {
      workspaceRoot: this.workspacePaths.workspaceRoot,
      cacheDir: this.workspacePaths.cacheDir,
    });
  }

  public async searchMaterials(payload: SearchMaterialsPayload): Promise<BridgeSuccess<SearchMaterialsResult>> {
    return this.call("search_materials", payload);
  }

  public async fetchStructure(payload: FetchStructurePayload): Promise<BridgeSuccess<FetchStructureResult>> {
    return this.call("fetch_structure", payload);
  }

  public async analyzeStructure(payload: AnalyzeStructurePayload): Promise<BridgeSuccess<AnalyzeStructureResult>> {
    return this.call("analyze_structure", payload);
  }

  public async compareCandidates(payload: CompareCandidatesPayload): Promise<BridgeSuccess<CompareCandidatesResult>> {
    return this.call("compare_candidates", payload);
  }

  public async aseRelax(payload: AseRelaxPayload): Promise<BridgeSuccess<AseRelaxResult>> {
    return this.call("ase_relax", payload, 5 * 60_000);
  }

  public async batchScreen(payload: BatchScreenPayload): Promise<BridgeSuccess<BatchScreenResult>> {
    return this.call("batch_screen", payload, 10 * 60_000);
  }

  public async exportReport(payload: ExportReportPayload): Promise<BridgeSuccess<ExportReportResult>> {
    return this.call("export_report", payload);
  }

  private async call<TPayload, TData>(
    action: BridgeAction,
    payload: TPayload,
    timeoutMs = DEFAULT_TIMEOUT_MS,
  ): Promise<BridgeSuccess<TData>> {
    const pythonPath = this.config.pythonPath?.trim();

    if (!pythonPath) {
      throw new ConfigurationError("No pythonPath is configured for Materials Lab.", {
        hint: "Set plugins.entries.materials-lab.config.pythonPath or run `openclaw materials setup-python`.",
      });
    }

    const request = createBridgeRequest(action, payload);

    return new Promise<BridgeSuccess<TData>>((resolve, reject) => {
      const child = spawn(pythonPath, ["-m", "materials_lab.worker"], {
        cwd: this.pluginRoot,
        env: {
          ...process.env,
          PYTHONPATH: mergePythonPath(this.pythonModuleRoot, process.env.PYTHONPATH),
          MATERIALS_PROJECT_API_KEY: this.config.mpApiKey,
          MATERIALS_LAB_WORKSPACE_ROOT: this.workspacePaths.workspaceRoot,
          MATERIALS_LAB_CACHE_DIR: this.workspacePaths.cacheDir,
        },
        stdio: ["pipe", "pipe", "pipe"],
      });

      let stdout = "";
      let stderr = "";
      let settled = false;

      const timeout = setTimeout(() => {
        child.kill("SIGKILL");
        if (!settled) {
          settled = true;
          reject(
            new PythonBridgeError(`Python worker timed out after ${timeoutMs} ms.`, {
              hint: "Reduce the requested workload or inspect the Python environment with `openclaw materials doctor`.",
              stderr,
              details: { action, timeoutMs },
            }),
          );
        }
      }, timeoutMs);

      child.stdout.setEncoding("utf8");
      child.stderr.setEncoding("utf8");
      child.stdout.on("data", (chunk) => {
        stdout += chunk;
      });
      child.stderr.on("data", (chunk) => {
        stderr += chunk;
      });

      child.on("error", (error) => {
        clearTimeout(timeout);
        if (settled) {
          return;
        }

        settled = true;
        reject(
          new PythonBridgeError(`Failed to start Python worker using ${pythonPath}.`, {
            hint: "Check pythonPath and run `openclaw materials doctor` for environment diagnostics.",
            stderr,
            cause: error,
          }),
        );
      });

      child.on("close", (code) => {
        clearTimeout(timeout);

        if (settled) {
          return;
        }

        settled = true;

        if (!stdout.trim() && code !== 0) {
          reject(
            new PythonBridgeError(`Python worker exited with code ${code ?? "unknown"}.`, {
              hint: "Inspect stderr output or run `openclaw materials doctor`.",
              stderr,
              details: { action, code },
            }),
          );
          return;
        }

        try {
          const parsed = parseBridgeResponse<TData>(stdout, stderr);
          resolve(parsed);
        } catch (error) {
          reject(error);
        }
      });

      child.stdin.write(JSON.stringify(request));
      child.stdin.end();
      this.logger.debug("Materials Lab bridge request sent.", { action, requestId: request.requestId });
    });
  }
}

function mergePythonPath(moduleRoot: string, existing?: string): string {
  return existing ? `${moduleRoot}${path.delimiter}${existing}` : moduleRoot;
}

function resolvePluginRoot(moduleUrl: string): string {
  const start = path.dirname(fileURLToPath(moduleUrl));
  let current = start;

  while (true) {
    if (existsSync(path.join(current, "openclaw.plugin.json")) && existsSync(path.join(current, "python"))) {
      return current;
    }

    const parent = path.dirname(current);
    if (parent === current) {
      break;
    }

    current = parent;
  }

  throw new ConfigurationError("Could not resolve the Materials Lab plugin root.", {
    hint: "Reinstall the plugin or ensure the package still contains openclaw.plugin.json and python/.",
  });
}
