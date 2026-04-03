import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { afterEach, describe, expect, it, vi } from "vitest";

import { resolveWorkspacePaths } from "../../src/core/paths.js";
import { createLogger } from "../../src/core/logger.js";
import type { MaterialsPluginContext } from "../../src/core/runtime-context.js";
import { ArtifactService } from "../../src/services/artifact-service.js";
import { NoteService } from "../../src/services/note-service.js";
import { createMaterialsSearchTool } from "../../src/tools/materials-search-mp.js";
import type { MaterialsLabPluginConfig, MaterialsWorkspacePaths } from "../../src/types/config.js";

describe("materials_search_mp", () => {
  const tempDirs: string[] = [];

  afterEach(async () => {
    await Promise.all(tempDirs.map(async (dir) => rm(dir, { recursive: true, force: true })));
    tempDirs.length = 0;
  });

  it("returns structured candidate summaries", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-search-tool-"));
    tempDirs.push(tempDir);
    const bridge = {
      searchMaterials: vi.fn().mockResolvedValue({
        ok: true,
        action: "search_materials",
        requestId: "req-1",
        summary: "Found 2 candidate materials using offline mock data.",
        data: {
          candidates: [
            { materialId: "mp-mock-hfo2", formula: "HfO2", source: "mock" },
            { materialId: "mp-mock-al2o3", formula: "Al2O3", source: "mock" },
          ],
          usedOfflineData: true,
        },
        artifacts: [],
        warnings: ["Using offline mock data."],
      }),
    };
    const context = createToolTestContext(tempDir, bridge);
    const tool = createMaterialsSearchTool(context);

    const result = await tool.execute("call-1", { limit: 2, allowOffline: true });

    expect(bridge.searchMaterials).toHaveBeenCalledWith({
      limit: 2,
      allowOffline: true,
    });
    expect(result.structuredContent.data.candidates).toHaveLength(2);
    expect(result.structuredContent.warnings).toContain("Using offline mock data.");
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
