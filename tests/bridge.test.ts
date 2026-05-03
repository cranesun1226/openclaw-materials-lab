import { mkdtemp, readFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import { createLogger } from "../src/core/logger.js";
import { resolveWorkspacePaths } from "../src/core/paths.js";
import { PythonBridgeService } from "../src/services/python-bridge.js";
import type { MaterialsLabPluginConfig } from "../src/types/config.js";

describe("Python bridge", () => {
  const tempDirs: string[] = [];

  afterEach(async () => {
    await Promise.all(tempDirs.map(async (dir) => rm(dir, { recursive: true, force: true })));
    tempDirs.length = 0;
  });

  it("talks to the local worker in offline mode", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-bridge-"));
    tempDirs.push(tempDir);
    const config: MaterialsLabPluginConfig = {
      pythonPath: "python3",
      mpApiKey: "",
      workspaceRoot: tempDir,
      cacheDir: path.join(tempDir, "cache"),
      defaultBatchLimit: 20,
      enableAseTools: false,
    };
    const bridge = new PythonBridgeService(config, resolveWorkspacePaths(config), createLogger());

    const ping = await bridge.ping();
    const search = await bridge.searchMaterials({
      elementsAll: ["O"],
      limit: 3,
      allowOffline: true,
    });

    expect(ping.summary).toContain("ready");
    expect(search.data.usedOfflineData).toBe(true);
    expect(search.data.candidates.length).toBeGreaterThan(0);
    expect(search.data.candidates[0]?.source).toBe("mock");
  });

  it("plans an approval-gated research loop", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-plan-"));
    tempDirs.push(tempDir);
    const config: MaterialsLabPluginConfig = {
      pythonPath: "python3",
      mpApiKey: "",
      workspaceRoot: tempDir,
      cacheDir: path.join(tempDir, "cache"),
      defaultBatchLimit: 20,
      enableAseTools: false,
    };
    const bridge = new PythonBridgeService(config, resolveWorkspacePaths(config), createLogger());
    const artifactDir = path.join(tempDir, "reports", "research-loop-plans");

    const result = await bridge.planResearchLoop({
      artifactDir,
      criteria: { preset: "high-k-dielectric" },
      budget: { maxCandidates: 1, maxCalculations: 3, maxWallTimeHours: 20 },
      candidates: [
        {
          materialId: "mp-mock-hfo2",
          formula: "HfO2",
          source: "mock",
          score: 0.9,
          rank: 1,
          reasons: ["test"],
          domainEvidence: {
            preset: "high-k-dielectric",
            tier: "proxy-shortlist",
            sourceLevel: "proxy-only",
            missingProperties: ["dielectricTotal", "bandOffsetElectronEv"],
          },
        },
      ],
    });

    expect(result.data.plan.executionStatus).toBe("planned-not-started");
    expect(result.data.plan.calculationQueue).toBeDefined();
    expect(result.artifacts).toContain(result.data.manifestPath);
    expect(await readFile(result.data.reportPath, "utf8")).toContain("Approval Gates");
  });
});
