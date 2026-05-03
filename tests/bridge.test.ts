import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
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

  it("talks to the local worker with explicit development fixture mode", async () => {
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
    expect(search.data.usedDevelopmentFixtureData).toBe(true);
    expect(search.data.candidates.length).toBeGreaterThan(0);
    expect(search.data.candidates[0]?.source).toBe("dev-fixture");
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
      researchGoal: "Find defensible high-k gate dielectric candidates with evidence-backed dielectric, leakage, and interface validation.",
      budget: { maxCandidates: 1, maxCalculations: 8, maxWallTimeHours: 40 },
      candidates: [
        {
          materialId: "fixture-hfo2",
          formula: "HfO2",
          source: "dev-fixture",
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
    expect(result.data.plan.protocolVersion).toBe("dynamic-research-protocol-v1");
    expect(result.data.plan.preset).toBe("dynamic");
    expect(result.data.plan.evidenceSchema).toBeDefined();
    expect(result.data.plan.calculationQueue).toBeDefined();
    expect(result.artifacts).toContain(result.data.manifestPath);
    expect(await readFile(result.data.reportPath, "utf8")).toContain("Approval Gates");

    const execution = await bridge.executeResearchPlan({
      planPath: result.data.manifestPath,
      artifactDir: path.join(tempDir, "reports", "research-loop-executions"),
      backend: "dev-smoke",
      allowBlockedDevSmoke: true,
      maxSteps: 3,
    });

    expect(execution.data.completedCalculations).toBeGreaterThan(0);
    expect(execution.data.propertyUpdates).toEqual([]);
    expect(execution.data.rerankingPayload).toBeUndefined();
    expect(await readFile(execution.data.reportPath, "utf8")).toContain("dev-smoke");

    const externalPreparation = await bridge.executeResearchPlan({
      planPath: result.data.manifestPath,
      artifactDir: path.join(tempDir, "reports", "research-loop-external-backends"),
      backend: "quantum-espresso",
      executionMode: "prepare",
      maxSteps: 8,
      backendConfig: { pseudoDir: "./pseudo", kpoints: "2 2 2 0 0 0", allowDevFixtures: true },
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

  it("compiles a dynamic research protocol before candidates exist", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-protocol-"));
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
    const result = await bridge.planResearchLoop({
      artifactDir: path.join(tempDir, "reports", "research-loop-plans"),
      researchGoal: "Design a lead-free moisture-stable photovoltaic absorber discovery campaign.",
      targetApplication: "thin-film solar absorber",
      constraints: ["lead-free", "moisture-stable"],
      candidateGeneration: {
        elementsExclude: ["Pb", "Cd"],
      },
      budget: { maxCandidates: 3, maxCalculations: 6, maxWallTimeHours: 24 },
      autonomyMode: "high-autonomy-plan",
    });

    const candidateGenerationPlan = result.data.plan.candidateGenerationPlan as Record<string, unknown>;
    const databaseQueries = candidateGenerationPlan.databaseQueries as unknown[];
    const evidenceSchema = result.data.plan.evidenceSchema as Array<Record<string, unknown>>;
    expect(result.data.plan.selectedCandidates).toEqual([]);
    expect(databaseQueries.length).toBeGreaterThan(0);
    expect(evidenceSchema.some((item) => item.id === "optical-absorption")).toBe(true);
    expect(await readFile(result.data.reportPath, "utf8")).toContain("Evidence Schema");
  });

  it("autonomously discovers a candidate pool when explicitly allowed", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-autonomous-discovery-"));
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
    const result = await bridge.planResearchLoop({
      artifactDir: path.join(tempDir, "reports", "autonomous-discovery-plans"),
      researchGoal: "Find lead-free high-k oxide gate dielectric candidates with evidence-ledger provenance.",
      constraints: ["lead-free", "oxide"],
      candidateGeneration: {
        autoDiscover: true,
        allowDevelopmentFixtures: true,
        formulas: ["HfO2", "Al2O3"],
        maxQueries: 3,
        perQueryLimit: 4,
      },
      budget: { maxCandidates: 2, maxCalculations: 10, maxWallTimeHours: 24 },
      autonomyMode: "high-autonomy-plan",
    });

    const plan = result.data.plan as Record<string, unknown>;
    const discovery = plan.autonomousDiscovery as Record<string, unknown>;
    const selectedCandidates = plan.selectedCandidates as Array<Record<string, unknown>>;
    const claimStatus = plan.claimStatus as Record<string, unknown>;

    expect(discovery.status).toBe("completed");
    expect(discovery.rankedCandidateCount).toBeGreaterThan(0);
    expect(selectedCandidates.length).toBeGreaterThan(0);
    expect(claimStatus.researchGradeClaimAllowed).toBe(false);
    expect(result.data.candidatePoolPath).toBeDefined();
    expect(result.data.evidenceLedgerPath).toBeDefined();
    expect(result.artifacts).toContain(result.data.candidatePoolPath);

    const candidatePoolText = await readFile(result.data.candidatePoolPath ?? "", "utf8");
    const ledgerText = await readFile(result.data.evidenceLedgerPath ?? "", "utf8");
    expect(candidatePoolText).toContain("dev-fixture");
    expect(ledgerText).toContain("blocks-research-grade-claim");
    expect(await readFile(result.data.reportPath, "utf8")).toContain("Autonomous Discovery");
  });

  it("evaluates claim gates from traceable evidence rows", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-claim-eval-"));
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
    await mkdir(path.join(tempDir, "reports"), { recursive: true });
    const artifactPath = path.join(tempDir, "reports", "parsed-output.json");
    const workflowPath = path.join(tempDir, "reports", "workflow-manifest.json");
    await writeFile(artifactPath, JSON.stringify({ targetProperty: 42 }), "utf8");
    await writeFile(workflowPath, JSON.stringify({ parser: "unit-test" }), "utf8");

    const result = await bridge.evaluateResearchClaim({
      artifactDir: path.join(tempDir, "reports", "claim-reviews"),
      candidateId: "fixture-hfo2",
      plan: {
        planId: "unit-claim-plan",
        selectedCandidates: [{ materialId: "fixture-hfo2", formula: "HfO2" }],
        claimPolicy: {
          requiredEvidenceRequirementIds: ["database-provenance", "target-property", "reproducibility"],
        },
        evidenceSchema: [
          {
            id: "database-provenance",
            label: "Database provenance",
            propertyKeys: ["databaseSummary"],
            evidenceTypes: ["database"],
            requiredForClaim: true,
          },
          {
            id: "target-property",
            label: "Target property",
            propertyKeys: ["targetProperty"],
            evidenceTypes: ["dft"],
            requiredForClaim: true,
          },
          {
            id: "reproducibility",
            label: "Reproducibility package",
            propertyKeys: ["workflowManifest"],
            evidenceTypes: ["workflow"],
            requiredForClaim: true,
          },
        ],
      },
      evidenceRows: [
        {
          candidateId: "fixture-hfo2",
          evidenceRequirementId: "database-provenance",
          status: "validated",
          sourceType: "database",
          source: "materials-project",
          confidence: "database-summary",
          propertyValues: { databaseSummary: "live database provenance attached" },
          queryIds: ["dbq-001"],
        },
        {
          candidateId: "fixture-hfo2",
          evidenceRequirementId: "target-property",
          status: "parsed-property",
          sourceType: "parsed-calculation",
          source: "unit-test-parser",
          confidence: "parsed-output",
          propertyValues: { targetProperty: 42 },
          artifactPath,
        },
        {
          candidateId: "fixture-hfo2",
          evidenceRequirementId: "reproducibility",
          status: "workflow-reproduced",
          sourceType: "workflow",
          source: "unit-test-workflow",
          confidence: "workflow-manifest",
          propertyValues: { workflowManifest: "present" },
          artifactPath: workflowPath,
        },
      ],
    });

    expect(result.data.claimStatus.currentLevel).toBe("research-grade-candidate");
    expect(result.data.claimStatus.researchGradeClaimAllowed).toBe(true);
    expect(result.data.missingEvidence).toEqual([]);
    expect(await readFile(result.data.reportPath, "utf8")).toContain("Research-grade claim allowed: `true`");
  });

  it("parses QE output into evidence rows for claim evaluation", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-ingest-evidence-"));
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
    const outputDir = path.join(tempDir, "reports", "qe-output");
    await mkdir(outputDir, { recursive: true });
    const qeOutput = path.join(outputDir, "pw.scf.out");
    await writeFile(
      qeOutput,
      [
        "Program PWSCF",
        "!    total energy              =     -123.456789 Ry",
        "highest occupied, lowest unoccupied level (ev):     4.1000    5.5000",
        "JOB DONE.",
        "",
      ].join("\n"),
      "utf8",
    );
    const plan = {
      planId: "qe-ingest-plan",
      selectedCandidates: [{ materialId: "mp-test", formula: "TestO2" }],
      claimPolicy: {
        requiredEvidenceRequirementIds: ["phase-stability"],
      },
      evidenceSchema: [
        {
          id: "phase-stability",
          label: "Phase stability",
          propertyKeys: ["totalEnergyEv"],
          evidenceTypes: ["dft"],
          requiredForClaim: true,
        },
      ],
    };

    const ingest = await bridge.ingestEvidence({
      artifactDir: path.join(tempDir, "reports", "evidence-ingestion"),
      plan,
      candidateId: "mp-test",
      parser: "quantum-espresso",
      artifactPaths: [qeOutput],
      evidenceRequirementId: "phase-stability",
    });

    expect(ingest.data.evidenceRowCount).toBeGreaterThan(0);
    expect(ingest.data.evidenceRows[0]?.propertyValues?.totalEnergyRy).toBe(-123.456789);
    expect(await readFile(ingest.data.reportPath, "utf8")).toContain("Evidence Ingestion");

    const claim = await bridge.evaluateResearchClaim({
      artifactDir: path.join(tempDir, "reports", "claim-reviews"),
      plan,
      candidateId: "mp-test",
      evidenceLedgerPath: ingest.data.evidenceLedgerPath,
    });

    expect(claim.data.claimStatus.researchGradeClaimAllowed).toBe(true);
    expect(claim.data.missingEvidence).toEqual([]);
  });
});
