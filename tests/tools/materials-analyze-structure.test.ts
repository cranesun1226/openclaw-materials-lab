import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { afterEach, describe, expect, it, vi } from "vitest";

import { resolveWorkspacePaths } from "../../src/core/paths.js";
import { createLogger } from "../../src/core/logger.js";
import type { MaterialsPluginContext } from "../../src/core/runtime-context.js";
import { ArtifactService } from "../../src/services/artifact-service.js";
import { NoteService } from "../../src/services/note-service.js";
import { createMaterialsAnalyzeStructureTool } from "../../src/tools/materials-analyze-structure.js";
import type { MaterialsLabPluginConfig, MaterialsWorkspacePaths } from "../../src/types/config.js";

describe("materials_analyze_structure", () => {
  const tempDirs: string[] = [];

  afterEach(async () => {
    await Promise.all(tempDirs.map(async (dir) => rm(dir, { recursive: true, force: true })));
    tempDirs.length = 0;
  });

  it("passes validated structure paths to the bridge", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-analyze-tool-"));
    tempDirs.push(tempDir);
    const structurePath = path.join(tempDir, "structures", "sample.json");
    await mkdir(path.dirname(structurePath), { recursive: true });
    await writeFile(
      structurePath,
      JSON.stringify({
        formula: "Si",
        lattice: [[5.43, 0, 0], [0, 5.43, 0], [0, 0, 5.43]],
        sites: [{ element: "Si", coords: [0, 0, 0] }],
      }),
    );

    const bridge = {
      analyzeStructure: vi.fn().mockResolvedValue({
        ok: true,
        action: "analyze_structure",
        requestId: "req-2",
        summary: "Si fallback analysis found 1 listed sites and elements Si.",
        data: {
          materialId: undefined,
          formula: "Si",
          summaryMetrics: { formula: "Si", numSites: 1 },
          readableSummary: "Si fallback analysis found 1 listed sites and elements Si.",
          plotPath: path.join(tempDir, "plots", "structure-metrics.png"),
          usedOfflineData: false,
        },
        artifacts: [path.join(tempDir, "plots", "structure-metrics.png")],
        warnings: [],
      }),
    };
    const context = createToolTestContext(tempDir, bridge);
    const tool = createMaterialsAnalyzeStructureTool(context);

    const result = await tool.execute("call-2", { structurePath, allowOffline: true });

    expect(bridge.analyzeStructure).toHaveBeenCalledWith({
      materialId: undefined,
      structurePath,
      artifactDir: path.join(tempDir, "plots"),
      allowOffline: true,
    });
    expect(result.structuredContent.data.formula).toBe("Si");
    expect(result.structuredContent.artifacts[0]?.kind).toBe("plot");
  });
});

function createToolTestContext(
  tempDir: string,
  bridge: Record<string, unknown>,
): MaterialsPluginContext {
  const baseConfig: MaterialsLabPluginConfig = {
    pythonPath: "python3",
    mpApiKey: "",
    workspaceRoot: tempDir,
    cacheDir: path.join(tempDir, "cache"),
    defaultBatchLimit: 20,
    enableAseTools: false,
  };
  const resolveConfig = (): MaterialsLabPluginConfig => baseConfig;
  const resolvePaths = (): MaterialsWorkspacePaths => resolveWorkspacePaths(baseConfig);
  const artifactService = new ArtifactService(resolvePaths());

  return {
    logger: createLogger(),
    loadConfigSource: () => undefined,
    resolveConfig,
    resolvePaths,
    getArtifactService: () => artifactService,
    getNoteService: () => new NoteService(artifactService),
    getBridge: () => bridge as MaterialsPluginContext["getBridge"] extends (...args: never[]) => infer T ? T : never,
    warmup: vi.fn(async () => undefined),
    stop: vi.fn(async () => undefined),
  };
}
