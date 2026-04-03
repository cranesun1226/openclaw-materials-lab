import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { afterEach, describe, expect, it, vi } from "vitest";

import { resolveWorkspacePaths } from "../../src/core/paths.js";
import { createLogger } from "../../src/core/logger.js";
import type { MaterialsPluginContext } from "../../src/core/runtime-context.js";
import { ArtifactService } from "../../src/services/artifact-service.js";
import { NoteService } from "../../src/services/note-service.js";
import { createMaterialsCompareCandidatesTool } from "../../src/tools/materials-compare-candidates.js";
import type { MaterialsLabPluginConfig, MaterialsWorkspacePaths } from "../../src/types/config.js";

describe("materials_compare_candidates", () => {
  const tempDirs: string[] = [];

  afterEach(async () => {
    await Promise.all(tempDirs.map(async (dir) => rm(dir, { recursive: true, force: true })));
    tempDirs.length = 0;
  });

  it("returns ranked candidates and plot artifacts", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-compare-tool-"));
    tempDirs.push(tempDir);
    const plotPath = path.join(tempDir, "plots", "candidate-ranking.png");
    const bridge = {
      compareCandidates: vi.fn().mockResolvedValue({
        ok: true,
        action: "compare_candidates",
        requestId: "req-3",
        summary: "Ranked 2 candidate materials.",
        data: {
          ranked: [
            { materialId: "mp-mock-hfo2", formula: "HfO2", source: "mock", score: 0.91, reasons: ["stable"], rank: 1 },
            { materialId: "mp-mock-al2o3", formula: "Al2O3", source: "mock", score: 0.87, reasons: ["wide gap"], rank: 2 },
          ],
          criteria: {
            stabilityWeight: 0.45,
            bandGapWeight: 0.35,
            densityWeight: 0.2,
            bandGapTargetEv: 3,
            densityTargetGcm3: 5,
          },
          plotPath,
        },
        artifacts: [plotPath],
        warnings: [],
      }),
    };
    const context = createToolTestContext(tempDir, bridge);
    const tool = createMaterialsCompareCandidatesTool(context);

    const result = await tool.execute("call-3", {
      candidates: [
        { materialId: "mp-mock-hfo2", formula: "HfO2", source: "mock" },
        { materialId: "mp-mock-al2o3", formula: "Al2O3", source: "mock" },
      ],
      topK: 2,
    });

    expect(bridge.compareCandidates).toHaveBeenCalled();
    expect(result.structuredContent.data.ranked[0]?.rank).toBe(1);
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
