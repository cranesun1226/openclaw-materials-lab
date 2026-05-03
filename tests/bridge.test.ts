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

    const execution = await bridge.executeResearchPlan({
      planPath: result.data.manifestPath,
      artifactDir: path.join(tempDir, "reports", "research-loop-executions"),
      backend: "local-surrogate",
      allowBlockedSurrogate: true,
      maxSteps: 3,
    });

    expect(execution.data.completedCalculations).toBeGreaterThan(0);
    expect(execution.data.propertyUpdates[0]?.propertyProvenance).toBeDefined();
    expect(await readFile(execution.data.reportPath, "utf8")).toContain("local-surrogate");

    const externalPreparation = await bridge.executeResearchPlan({
      planPath: result.data.manifestPath,
      artifactDir: path.join(tempDir, "reports", "research-loop-external-backends"),
      backend: "quantum-espresso",
      executionMode: "prepare",
      maxSteps: 2,
      backendConfig: { pseudoDir: "./pseudo", kpoints: "2 2 2 0 0 0" },
    });

    expect(externalPreparation.data.completedCalculations).toBe(0);
    expect(externalPreparation.data.preparedCalculations).toBeGreaterThan(0);
    expect(externalPreparation.data.inputPaths?.some((item) => item.endsWith("pw.scf.in"))).toBe(true);
    expect(await readFile(externalPreparation.data.reportPath, "utf8")).toContain("Quantum ESPRESSO");
    const scfInput = externalPreparation.data.inputPaths?.find((item) => item.endsWith("pw.scf.in"));
    const scfText = await readFile(scfInput ?? "", "utf8");
    expect(scfText).toContain("ATOMIC_SPECIES");
    expect(scfText).toContain("Hf 178.490000 Hf.UPF");
  });
});
