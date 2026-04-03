import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { afterEach, describe, expect, it, vi } from "vitest";

import { resolveWorkspacePaths } from "../../src/core/paths.js";
import { createLogger } from "../../src/core/logger.js";
import type { MaterialsPluginContext } from "../../src/core/runtime-context.js";
import { ArtifactService } from "../../src/services/artifact-service.js";
import { NoteService } from "../../src/services/note-service.js";
import { createMaterialsExportReportTool } from "../../src/tools/materials-export-report.js";
import type { MaterialsLabPluginConfig, MaterialsWorkspacePaths } from "../../src/types/config.js";

describe("materials_export_report", () => {
  const tempDirs: string[] = [];

  afterEach(async () => {
    await Promise.all(tempDirs.map(async (dir) => rm(dir, { recursive: true, force: true })));
    tempDirs.length = 0;
  });

  it("passes sanitized workspace paths to the bridge", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-export-tool-"));
    tempDirs.push(tempDir);
    const notePath = path.join(tempDir, "notes", "existing-note.md");
    const artifactPath = path.join(tempDir, "plots", "figure.png");
    await mkdir(path.dirname(notePath), { recursive: true });
    await mkdir(path.dirname(artifactPath), { recursive: true });
    await writeFile(notePath, "# note\n", "utf8");
    await writeFile(artifactPath, "fake", "utf8");

    const bridge = {
      exportReport: vi.fn().mockResolvedValue({
        ok: true,
        action: "export_report",
        requestId: "req-4",
        summary: "Exported markdown report.",
        data: {
          outputPath: path.join(tempDir, "reports", "demo-report.md"),
          references: [notePath, artifactPath],
        },
        artifacts: [path.join(tempDir, "reports", "demo-report.md")],
        warnings: [],
      }),
    };
    const context = createToolTestContext(tempDir, bridge);
    const tool = createMaterialsExportReportTool(context);

    const result = await tool.execute("call-4", {
      title: "Demo report",
      goal: "Compare dielectric candidates.",
      evaluationCriteria: ["stability", "band gap"],
      rankedCandidates: [
        {
          materialId: "mp-mock-hfo2",
          formula: "HfO2",
          source: "mock",
          score: 0.91,
          rank: 1,
          reasons: ["stable"],
        },
      ],
      notePaths: [notePath],
      artifactPaths: [artifactPath],
    });

    expect(bridge.exportReport).toHaveBeenCalledWith(
      expect.objectContaining({
        notePaths: [notePath],
        artifactPaths: [artifactPath],
      }),
    );
    expect(result.structuredContent.artifacts[0]?.kind).toBe("report");
  });

  it("rejects note paths outside the workspace", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-export-tool-"));
    tempDirs.push(tempDir);
    const context = createToolTestContext(tempDir, {
      exportReport: vi.fn(),
    });
    const tool = createMaterialsExportReportTool(context);

    await expect(
      tool.execute("call-5", {
        title: "Bad report",
        goal: "Compare dielectric candidates.",
        evaluationCriteria: ["stability"],
        rankedCandidates: [
          {
            materialId: "mp-mock-hfo2",
            formula: "HfO2",
            source: "mock",
            score: 0.91,
            rank: 1,
            reasons: ["stable"],
          },
        ],
        notePaths: [path.join(os.tmpdir(), "outside-note.md")],
      }),
    ).rejects.toThrow("must stay inside");
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
