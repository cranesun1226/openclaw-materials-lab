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
    expect(result.data.plan.methodRegistry).toBeDefined();
    expect(result.data.plan.literatureEvidencePipeline).toBeDefined();
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

    await writeFile(
      path.join(path.dirname(scfInput ?? ""), "pw.scf.out"),
      ["!    total energy              =     -20.000000 Ry", "JOB DONE.", ""].join("\n"),
      "utf8",
    );
    const monitored = await bridge.executeResearchPlan({
      planPath: result.data.manifestPath,
      artifactDir: path.join(tempDir, "reports", "research-loop-monitor"),
      backend: "quantum-espresso",
      executionMode: "monitor",
      executionManifestPath: externalPreparation.data.manifestPath,
      backendConfig: { parseOutputs: true },
    });

    expect(monitored.data.completedCalculations).toBeGreaterThan(0);
    expect(monitored.data.parsedEvidenceRows).toBeGreaterThan(0);
    expect(monitored.data.evidenceLedgerPath).toBeDefined();
    expect(await readFile(monitored.data.reportPath, "utf8")).toContain("Backend Monitor");
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

  it("searches literature metadata into evidence rows using explicit development fixtures", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-literature-search-"));
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
    const plan = {
      planId: "literature-plan",
      selectedCandidates: [{ materialId: "mp-lit", formula: "NiO" }],
      literatureReviewPlan: { queries: ["NiO oxygen evolution catalyst benchmark"] },
      evidenceSchema: [
        {
          id: "literature-benchmark",
          label: "Literature benchmark",
          propertyKeys: ["literatureBaseline"],
          evidenceTypes: ["literature"],
          requiredForClaim: true,
        },
      ],
    };

    const result = await bridge.searchLiterature({
      artifactDir: path.join(tempDir, "reports", "literature-search"),
      plan,
      candidateId: "mp-lit",
      allowNetwork: false,
      allowDevelopmentFixtures: true,
      providers: ["openalex"],
      maxResultsPerQuery: 2,
    });

    expect(result.data.usedDevelopmentFixtureData).toBe(true);
    expect(result.data.recordCount).toBeGreaterThan(0);
    expect(result.data.evidenceRowCount).toBeGreaterThan(0);
    expect(result.data.evidenceRows[0]?.source).toBe("development-literature-fixture");
    expect(await readFile(result.data.reportPath, "utf8")).toContain("Literature Evidence Search");
  });

  it("builds an evidence gap closure plan and can run fixture literature search without unlocking claims", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-gap-closure-"));
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
    const plan = {
      planId: "gap-closure-plan",
      selectedCandidates: [{ materialId: "mp-gap", formula: "NiO" }],
      literatureReviewPlan: { queries: ["NiO catalyst stability benchmark"] },
      claimPolicy: {
        requiredEvidenceRequirementIds: ["literature-benchmark", "surface-activity", "reproducibility"],
      },
      evidenceSchema: [
        {
          id: "literature-benchmark",
          label: "Literature benchmark",
          propertyKeys: ["literatureBaseline"],
          evidenceTypes: ["literature"],
          requiredForClaim: true,
        },
        {
          id: "surface-activity",
          label: "Surface activity",
          propertyKeys: ["adsorptionEnergyEv"],
          evidenceTypes: ["dft"],
          requiredForClaim: true,
        },
        {
          id: "reproducibility",
          label: "Reproducibility",
          propertyKeys: ["workflowManifest"],
          evidenceTypes: ["workflow"],
          requiredForClaim: true,
        },
      ],
    };

    const result = await bridge.closeEvidenceGaps({
      artifactDir: path.join(tempDir, "reports", "gap-closure"),
      plan,
      candidateId: "mp-gap",
      runLiteratureSearch: true,
      allowNetwork: false,
      allowDevelopmentFixtures: true,
      providers: ["crossref"],
      maxLiteratureQueries: 2,
      maxResultsPerQuery: 1,
    });

    const closurePlan = result.data.closurePlan as Record<string, unknown>;
    const actions = closurePlan.actions as Array<Record<string, unknown>>;
    const nextTools = closurePlan.nextToolSequence as string[];

    expect(result.data.claimStatus.researchGradeClaimAllowed).toBe(false);
    expect(result.data.literatureSearch?.usedDevelopmentFixtureData).toBe(true);
    expect(actions.some((item) => item.actionType === "prepare-backend-calculation")).toBe(true);
    expect(nextTools).toContain("materials_search_literature");
    expect(nextTools).toContain("materials_execute_research_plan");
    expect(await readFile(result.data.reportPath, "utf8")).toContain("Evidence Gap Closure Plan");
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

  it("parses literature, VASP, and MD-style evidence and blocks conflicted claims", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-expanded-evidence-"));
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
    const outputDir = path.join(tempDir, "reports", "expanded-output");
    await mkdir(outputDir, { recursive: true });
    const outcar = path.join(outputDir, "OUTCAR");
    const literature = path.join(outputDir, "literature-review.md");
    await writeFile(
      outcar,
      [
        "free  energy   TOTEN  =      -10.500000 eV",
        "E-fermi : 5.4321",
        "band gap: 1.20 eV",
        "surface energy = 1.50 J/m^2",
        "adsorption energy = -0.42 eV",
        "freq ( 1) = 18.0 [cm-1]",
        "freq ( 2) = -12.0 [cm-1]",
        "temperature = 300 K",
        "temperature = 310 K",
        "diffusion coefficient = 1.0e-6 cm^2/s",
        "",
      ].join("\n"),
      "utf8",
    );
    await writeFile(
      literature,
      [
        "Catalyst benchmark evidence for mp-surface",
        "DOI: 10.1234/example.materials.2026",
        "mp-surface reported overpotential of 0.31 V and adsorption energy = -0.20 eV.",
        "| material | property | value |",
        "| mp-surface | overpotentialV | 0.31 |",
        "",
      ].join("\n"),
      "utf8",
    );
    const plan = {
      planId: "expanded-evidence-plan",
      selectedCandidates: [{ materialId: "mp-surface", formula: "NiO" }],
      claimPolicy: {
        requiredEvidenceRequirementIds: ["surface-activity"],
      },
      evidenceSchema: [
        {
          id: "surface-activity",
          label: "Surface activity",
          propertyKeys: ["adsorptionEnergyEv"],
          evidenceTypes: ["dft"],
          requiredForClaim: true,
        },
      ],
    };

    const vasp = await bridge.ingestEvidence({
      artifactDir: path.join(tempDir, "reports", "evidence-ingestion"),
      plan,
      candidateId: "mp-surface",
      parser: "vasp",
      artifactPaths: [outcar],
    });
    expect(vasp.data.evidenceRows.some((row) => row.propertyValues?.surfaceEnergyJm2 === 1.5)).toBe(true);
    expect(vasp.data.evidenceRows.some((row) => row.propertyValues?.imaginaryModeCount === 1)).toBe(true);
    expect(vasp.data.evidenceRows.some((row) => row.propertyValues?.averageTemperatureK === 305)).toBe(true);

    const lit = await bridge.ingestEvidence({
      artifactDir: path.join(tempDir, "reports", "literature-ingestion"),
      plan,
      candidateId: "mp-surface",
      parser: "literature-markdown",
      artifactPaths: [literature],
      evidenceLedgerPath: vasp.data.evidenceLedgerPath,
    });
    expect(lit.data.evidenceRows[0]?.citation).toContain("10.1234/example.materials.2026");

    const claim = await bridge.evaluateResearchClaim({
      artifactDir: path.join(tempDir, "reports", "claim-reviews"),
      plan,
      candidateId: "mp-surface",
      evidenceRows: [
        {
          candidateId: "mp-surface",
          evidenceRequirementId: "surface-activity",
          status: "parsed-property",
          sourceType: "parsed-calculation",
          source: "vasp",
          confidence: "parsed-output",
          propertyValues: { adsorptionEnergyEv: -0.20 },
          artifactPath: outcar,
        },
        {
          candidateId: "mp-surface",
          evidenceRequirementId: "surface-activity",
          status: "parsed-property",
          sourceType: "parsed-calculation",
          source: "vasp-repeat",
          confidence: "parsed-output",
          propertyValues: { adsorptionEnergyEv: -0.80 },
          artifactPath: outcar,
        },
      ],
    });

    expect(claim.data.claimStatus.researchGradeClaimAllowed).toBe(false);
    expect(claim.data.uncertaintySummary?.materialConflicts).toBeDefined();
    expect(claim.data.auditCertificate?.decision).toBe("block");
    expect(await readFile(claim.data.reportPath, "utf8")).toContain("Audit Certificate");
  });
});
