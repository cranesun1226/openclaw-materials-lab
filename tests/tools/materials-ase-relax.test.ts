import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { afterEach, describe, expect, it, vi } from "vitest";

import { createLogger } from "../../src/core/logger.js";
import { resolveWorkspacePaths } from "../../src/core/paths.js";
import type { MaterialsPluginContext } from "../../src/core/runtime-context.js";
import { ArtifactService } from "../../src/services/artifact-service.js";
import { NoteService } from "../../src/services/note-service.js";
import { createMaterialsAseRelaxTool } from "../../src/tools/materials-ase-relax.js";
import type { MaterialsLabPluginConfig, MaterialsWorkspacePaths } from "../../src/types/config.js";

describe("materials_ase_relax", () => {
  const tempDirs: string[] = [];

  afterEach(async () => {
    await Promise.all(tempDirs.map(async (dir) => rm(dir, { recursive: true, force: true })));
    tempDirs.length = 0;
  });

  it("passes SevenNet options through to the Python bridge", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-ase-tool-"));
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
      aseRelax: vi.fn().mockResolvedValue({
        ok: true,
        action: "ase_relax",
        requestId: "req-ase",
        summary: "ASE relaxation workflow completed.",
        data: {
          summaryMetrics: {
            executed: true,
            calculator: "SevenNet",
            sevenNetModel: "7net-omni",
            sevenNetModal: "mpa",
            device: "cpu",
            finalEnergyEv: -1.23,
            maxForceEvA: 0.02,
          },
          relaxedStructurePath: path.join(tempDir, "plots", "relaxed.xyz"),
          trajectoryPath: undefined,
          usedOfflineData: false,
        },
        artifacts: [path.join(tempDir, "plots", "relaxed.xyz")],
        warnings: [],
      }),
    };
    const context = createToolTestContext(tempDir, bridge);
    const tool = createMaterialsAseRelaxTool(context);

    const result = await tool.execute("call-ase", {
      structurePath,
      calculator: "SevenNet",
      sevenNetModel: "7net-omni",
      sevenNetModal: "mpa",
      device: "cpu",
      steps: 25,
      fmaxEvA: 0.03,
      allowOffline: true,
    });

    expect(bridge.aseRelax).toHaveBeenCalledWith({
      structurePath,
      artifactDir: path.join(tempDir, "plots"),
      calculator: "SevenNet",
      sevenNetModel: "7net-omni",
      sevenNetModal: "mpa",
      device: "cpu",
      steps: 25,
      fmaxEvA: 0.03,
      allowOffline: true,
    });
    expect(result.structuredContent.data.summaryMetrics.calculator).toBe("SevenNet");
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
    enableAseTools: true,
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
