import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { runCommandWithTimeout } from "openclaw/plugin-sdk/process-runtime";

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
  CloseEvidenceGapsPayload,
  CloseEvidenceGapsResult,
  CompareCandidatesPayload,
  CompareCandidatesResult,
  ExecuteResearchPlanPayload,
  ExecuteResearchPlanResult,
  EvaluateResearchClaimPayload,
  EvaluateResearchClaimResult,
  ExportReportPayload,
  ExportReportResult,
  FetchStructurePayload,
  FetchStructureResult,
  IngestEvidencePayload,
  IngestEvidenceResult,
  PlanResearchLoopPayload,
  PlanResearchLoopResult,
  SearchLiteraturePayload,
  SearchLiteratureResult,
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

  public async planResearchLoop(payload: PlanResearchLoopPayload): Promise<BridgeSuccess<PlanResearchLoopResult>> {
    return this.call("plan_research_loop", payload);
  }

  public async searchLiterature(payload: SearchLiteraturePayload): Promise<BridgeSuccess<SearchLiteratureResult>> {
    return this.call("search_literature", payload);
  }

  public async evaluateResearchClaim(
    payload: EvaluateResearchClaimPayload,
  ): Promise<BridgeSuccess<EvaluateResearchClaimResult>> {
    return this.call("evaluate_research_claim", payload);
  }

  public async closeEvidenceGaps(
    payload: CloseEvidenceGapsPayload,
  ): Promise<BridgeSuccess<CloseEvidenceGapsResult>> {
    return this.call("close_evidence_gaps", payload);
  }

  public async ingestEvidence(payload: IngestEvidencePayload): Promise<BridgeSuccess<IngestEvidenceResult>> {
    return this.call("ingest_evidence", payload);
  }

  public async executeResearchPlan(payload: ExecuteResearchPlanPayload): Promise<BridgeSuccess<ExecuteResearchPlanResult>> {
    return this.call("execute_research_plan", payload, 10 * 60_000);
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

    let result: Awaited<ReturnType<typeof runCommandWithTimeout>>;
    try {
      result = await runCommandWithTimeout([pythonPath, "-m", "materials_lab.worker"], {
        cwd: this.pluginRoot,
        env: {
          PYTHONPATH: mergePythonPath(this.pythonModuleRoot, process.env.PYTHONPATH),
          MATERIALS_PROJECT_API_KEY: this.config.mpApiKey,
          MATERIALS_LAB_WORKSPACE_ROOT: this.workspacePaths.workspaceRoot,
          MATERIALS_LAB_CACHE_DIR: this.workspacePaths.cacheDir,
        },
        input: JSON.stringify(request),
        timeoutMs,
      });
    } catch (error) {
      throw new PythonBridgeError(`Failed to start Python worker using ${pythonPath}.`, {
        hint: "Check pythonPath and run `openclaw materials doctor` for environment diagnostics.",
        cause: error,
      });
    }

    this.logger.debug("Materials Lab bridge request sent.", { action, requestId: request.requestId });

    if (result.termination === "timeout" || result.termination === "no-output-timeout") {
      throw new PythonBridgeError(`Python worker timed out after ${timeoutMs} ms.`, {
        hint: "Reduce the requested workload or inspect the Python environment with `openclaw materials doctor`.",
        stderr: result.stderr,
        details: { action, timeoutMs },
      });
    }

    if (!result.stdout.trim() && result.code !== 0) {
      throw new PythonBridgeError(`Python worker exited with code ${result.code ?? "unknown"}.`, {
        hint: "Inspect stderr output or run `openclaw materials doctor`.",
        stderr: result.stderr,
        details: { action, code: result.code },
      });
    }

    return parseBridgeResponse<TData>(result.stdout, result.stderr);
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
