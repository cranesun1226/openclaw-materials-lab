import fs from "node:fs/promises";
import fsSync from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { resolveWorkspacePaths } from "../../dist/src/core/paths.js";
import { ArtifactService } from "../../dist/src/services/artifact-service.js";
import { PythonBridgeService } from "../../dist/src/services/python-bridge.js";

const repoRoot = path.resolve(path.join(path.dirname(fileURLToPath(import.meta.url)), "../.."));
const runRoot = path.join(repoRoot, "materials-lab-runs", "dynamic-photovoltaic-protocol-e2e-20260503");
const openclawConfigPath = path.join(os.homedir(), ".openclaw", "openclaw.json");
const startedAt = new Date().toISOString();

const topic = "Design a lead-free moisture-stable photovoltaic absorber discovery campaign.";
const targetApplication = "thin-film solar absorber";
const constraints = ["lead-free", "moisture-stable", "Earth-abundant preferred", "no research-grade claim without parsed evidence"];
const artifactPaths = new Set();
const checks = [];
const liveSearches = [];
const structureChecks = [];

const openclawConfig = await loadOpenClawConfig(openclawConfigPath);
const pluginConfig = openclawConfig.plugins?.entries?.["materials-lab"]?.config ?? {};
const config = {
  pythonPath: pluginConfig.pythonPath || "python3",
  mpApiKey: pluginConfig.mpApiKey || "",
  workspaceRoot: runRoot,
  cacheDir: path.join(runRoot, "cache"),
  defaultBatchLimit: pluginConfig.defaultBatchLimit ?? 20,
  enableAseTools: pluginConfig.enableAseTools ?? false,
};
const paths = resolveWorkspacePaths(config);
const logger = {
  debug() {},
  info() {},
  warn(message, details) {
    console.warn("[materials-lab]", message, details ?? "");
  },
  error(message, details) {
    console.error("[materials-lab]", message, details ?? "");
  },
};
const artifactService = new ArtifactService(paths);
const bridge = new PythonBridgeService(config, paths, logger);

await artifactService.ensureReady();
await fs.mkdir(paths.reportsDir, { recursive: true });

try {
  const ping = await bridge.ping();
  check("bridge-ping", ping.summary.includes("ready"), ping.summary);

  const liveCandidates = await tryLiveMaterialsProjectSearch();
  let candidateSourceMode = "materials-project-live";
  let candidates = liveCandidates;
  let fixtureFallback = null;

  if (candidates.length === 0) {
    candidateSourceMode = "dev-fixture-smoke";
    fixtureFallback = await bridge.searchMaterials({
      elementsAny: ["Si", "O"],
      limit: 4,
      allowOffline: true,
    });
    candidates = fixtureFallback.data.candidates ?? [];
    check("dev-fixture-fallback", fixtureFallback.data.usedDevelopmentFixtureData === true, fixtureFallback.summary);
  }

  check("candidate-pool", candidates.length > 0, `candidateCount=${candidates.length}; sourceMode=${candidateSourceMode}`);

  if (candidateSourceMode === "materials-project-live") {
    await tryLiveStructureValidation(candidates[0]);
  }

  const protocolOnly = await bridge.planResearchLoop({
    artifactDir: path.join(paths.reportsDir, "dynamic-protocol-no-candidates"),
    researchGoal: topic,
    targetApplication,
    constraints,
    literatureQueries: [
      "lead-free moisture-stable photovoltaic absorbers review",
      "thin-film solar absorber defect tolerance moisture stability",
    ],
    databaseQueries: [
      "lead-free photovoltaic absorber candidates band gap 1.0-1.8 eV",
      "stable chalcogenide oxide photovoltaic absorbers Materials Project",
    ],
    candidateGeneration: {
      strategy: "discover candidates from Materials Project and literature before ranking",
      elementsExclude: ["Pb", "Cd", "Hg"],
      targetBandGapEv: [1.0, 1.8],
      requireEnergyAboveHullEvMax: 0.08,
    },
    validationMethods: ["database", "literature", "dft", "experiment"],
    budget: { maxCandidates: 4, maxCalculations: 8, maxWallTimeHours: 36, maxLoopIterations: 2 },
    autonomyMode: "high-autonomy-plan",
    approvalPolicy: "approval-required",
  });
  recordArtifacts(protocolOnly.artifacts);
  check("protocol-compiler-version", protocolOnly.data.plan.protocolVersion === "dynamic-research-protocol-v1", protocolOnly.summary);
  check("protocol-without-candidates", protocolOnly.data.plan.selectedCandidates.length === 0, "selectedCandidates=0");
  check(
    "photovoltaic-evidence-schema",
    protocolOnly.data.plan.evidenceSchema.some((item) => item.id === "optical-absorption"),
    protocolOnly.data.plan.evidenceSchema.map((item) => item.id).join(", "),
  );

  const rankedCandidates = rankForPhotovoltaicProtocol(candidates).slice(0, 3);
  const candidateBackedPlan = await bridge.planResearchLoop({
    artifactDir: path.join(paths.reportsDir, "dynamic-protocol-candidate-backed"),
    researchGoal: topic,
    targetApplication,
    hypothesis:
      "A bounded autonomous agent can compile an evidence contract and backend-ready workflow before claiming any photovoltaic absorber discovery.",
    constraints,
    candidates: rankedCandidates,
    candidateGeneration: {
      strategy: "use live database candidates when available; otherwise use explicit development fixture smoke data only",
      elementsExclude: ["Pb", "Cd", "Hg"],
      targetBandGapEv: [1.0, 1.8],
      requireEnergyAboveHullEvMax: 0.08,
    },
    budget: {
      maxCandidates: Math.min(2, rankedCandidates.length),
      maxCalculations: 14,
      maxWallTimeHours: 72,
      maxLoopIterations: 2,
      allowExpensiveCalculations: false,
    },
    autonomyMode: "high-autonomy-plan",
    approvalPolicy: "approval-required",
  });
  recordArtifacts(candidateBackedPlan.artifacts);
  check("candidate-backed-plan", candidateBackedPlan.data.plan.selectedCandidates.length > 0, candidateBackedPlan.summary);
  check(
    "claim-policy-present",
    Array.isArray(candidateBackedPlan.data.plan.claimPolicy?.researchGradeRequires),
    "researchGradeRequires is present",
  );
  check(
    "approval-gates-present",
    (candidateBackedPlan.data.plan.approvalGates ?? []).length >= 3,
    `approvalGates=${candidateBackedPlan.data.plan.approvalGates.length}`,
  );

  const devSmoke = await bridge.executeResearchPlan({
    planPath: candidateBackedPlan.data.manifestPath,
    artifactDir: path.join(paths.reportsDir, "dynamic-protocol-dev-smoke-execution"),
    backend: "dev-smoke",
    allowBlockedDevSmoke: true,
    maxSteps: 8,
  });
  recordArtifacts(devSmoke.artifacts);
  recordArtifacts(devSmoke.data.resultPaths);
  check("dev-smoke-completed", devSmoke.data.completedCalculations > 0, devSmoke.summary);
  check("dev-smoke-no-property-claims", (devSmoke.data.propertyUpdates ?? []).length === 0, "propertyUpdates=0");

  const qePrepare = await bridge.executeResearchPlan({
    planPath: candidateBackedPlan.data.manifestPath,
    artifactDir: path.join(paths.reportsDir, "dynamic-protocol-qe-prepare"),
    backend: "quantum-espresso",
    executionMode: "prepare",
    allowExecution: false,
    maxSteps: 14,
    backendConfig: {
      pseudoDir: "./pseudo",
      kpoints: "2 2 2 0 0 0",
      allowDevFixtures: candidateSourceMode === "dev-fixture-smoke",
    },
  });
  recordArtifacts(qePrepare.artifacts);
  recordArtifacts(qePrepare.data.resultPaths);
  recordArtifacts(qePrepare.data.inputPaths);
  check("qe-inputs-prepared", qePrepare.data.preparedCalculations > 0, qePrepare.summary);
  check("qe-no-submission", qePrepare.data.submittedCalculations === 0, "submittedCalculations=0");
  const scfInputPath = (qePrepare.data.inputPaths ?? []).find((item) => item.endsWith("pw.scf.in"));
  const scfInput = scfInputPath ? await fs.readFile(scfInputPath, "utf8") : "";
  check("qe-scf-input-contains-atomic-species", scfInput.includes("ATOMIC_SPECIES"), scfInputPath ?? "no pw.scf.in");

  const summary = {
    status: checks.every((item) => item.ok) ? "passed" : "failed",
    startedAt,
    completedAt: new Date().toISOString(),
    runRoot,
    topic,
    targetApplication,
    constraints,
    openclaw: {
      configPath: openclawConfigPath,
      materialsLabConfigured: Boolean(openclawConfig.plugins?.entries?.["materials-lab"]),
      materialsProjectApiKeyConfigured: Boolean(pluginConfig.mpApiKey),
      pythonPath: config.pythonPath,
    },
    candidateSourceMode,
    liveSearches,
    fixtureFallback: fixtureFallback
      ? {
          summary: fixtureFallback.summary,
          usedDevelopmentFixtureData: fixtureFallback.data.usedDevelopmentFixtureData,
          candidateCount: fixtureFallback.data.candidates?.length ?? 0,
          candidateIds: (fixtureFallback.data.candidates ?? []).map((candidate) => candidate.materialId),
        }
      : null,
    structureChecks,
    protocolOnly: summarizePlan(protocolOnly),
    candidateBackedPlan: summarizePlan(candidateBackedPlan),
    devSmoke: summarizeExecution(devSmoke),
    quantumEspressoPrepare: summarizeExecution(qePrepare),
    checks,
    artifactPaths: [...artifactPaths].sort(),
    artifactsExist: await validateArtifacts([...artifactPaths]),
    verdict:
      candidateSourceMode === "materials-project-live"
        ? "OpenClaw Materials Lab compiled and exercised a live-data dynamic research protocol. No research-grade discovery claim was made."
        : "OpenClaw Materials Lab compiled and exercised the dynamic protocol with explicit development fixture data only. This verifies plumbing, not materials evidence.",
  };
  const summaryPath = path.join(paths.reportsDir, "live-openclaw-dynamic-photovoltaic-e2e-summary.json");
  const reportPath = path.join(paths.reportsDir, "live-openclaw-dynamic-photovoltaic-e2e-process.md");
  await fs.writeFile(summaryPath, JSON.stringify(summary, null, 2) + "\n", "utf8");
  await fs.writeFile(reportPath, renderReport(summary), "utf8");
  console.log(JSON.stringify({ status: summary.status, candidateSourceMode, summaryPath, reportPath }, null, 2));
  if (summary.status !== "passed") {
    process.exitCode = 1;
  }
} catch (error) {
  const failure = {
    status: "failed",
    startedAt,
    completedAt: new Date().toISOString(),
    runRoot,
    topic,
    error: sanitizeError(error),
    checks,
    liveSearches,
    structureChecks,
  };
  const failurePath = path.join(paths.reportsDir, "live-openclaw-dynamic-photovoltaic-e2e-failure.json");
  await fs.writeFile(failurePath, JSON.stringify(failure, null, 2) + "\n", "utf8");
  console.error(JSON.stringify({ status: "failed", failurePath, error: failure.error }, null, 2));
  process.exitCode = 1;
}

async function loadOpenClawConfig(configPath) {
  if (!fsSync.existsSync(configPath)) {
    return {};
  }
  return JSON.parse(await fs.readFile(configPath, "utf8"));
}

async function tryLiveMaterialsProjectSearch() {
  if (!config.mpApiKey) {
    liveSearches.push({ status: "skipped", reason: "Materials Project API key is not configured." });
    return [];
  }
  const queries = [
    {
      label: "silicon absorber baseline",
      payload: { formula: "Si", maxEnergyAboveHullEv: 0.05, minBandGapEv: 0.5, maxBandGapEv: 2.2, limit: 8, allowOffline: false },
    },
    {
      label: "chalcopyrite selenide absorber family",
      payload: {
        elementsAll: ["Cu", "In", "Se"],
        maxEnergyAboveHullEv: 0.08,
        minBandGapEv: 0.7,
        maxBandGapEv: 2.2,
        limit: 8,
        allowOffline: false,
      },
    },
    {
      label: "kesterite sulfide absorber family",
      payload: {
        elementsAll: ["Cu", "Zn", "Sn", "S"],
        maxEnergyAboveHullEv: 0.08,
        minBandGapEv: 0.7,
        maxBandGapEv: 2.2,
        limit: 8,
        allowOffline: false,
      },
    },
  ];
  const byId = new Map();
  for (const query of queries) {
    try {
      const result = await bridge.searchMaterials(query.payload);
      const candidates = result.data.candidates ?? [];
      liveSearches.push({
        label: query.label,
        status: "ok",
        summary: result.summary,
        usedOfflineData: result.data.usedOfflineData,
        candidateCount: candidates.length,
        candidateIds: candidates.map((candidate) => candidate.materialId),
      });
      check(`live-search-${query.label}`, result.data.usedOfflineData === false, `candidateCount=${candidates.length}`);
      for (const candidate of candidates) {
        if (candidate?.materialId && !byId.has(candidate.materialId)) {
          byId.set(candidate.materialId, candidate);
        }
      }
    } catch (error) {
      liveSearches.push({ label: query.label, status: "failed", error: sanitizeError(error) });
      return [];
    }
  }
  return [...byId.values()];
}

async function tryLiveStructureValidation(candidate) {
  if (!candidate?.materialId) {
    return;
  }
  const structureDir = path.join(paths.structuresDir, slugForPath(candidate.materialId));
  try {
    const fetched = await bridge.fetchStructure({
      materialId: candidate.materialId,
      format: "both",
      artifactDir: structureDir,
      allowOffline: false,
    });
    recordArtifacts(fetched.artifacts);
    structureChecks.push({
      materialId: candidate.materialId,
      status: "fetched",
      summary: fetched.summary,
      usedOfflineData: fetched.data.usedOfflineData,
      structurePath: fetched.data.structurePath,
      cifPath: fetched.data.cifPath,
    });
    check("live-structure-fetch", fetched.data.usedOfflineData === false, fetched.summary);
  } catch (error) {
    structureChecks.push({ materialId: candidate.materialId, status: "failed", error: sanitizeError(error) });
    check("live-structure-fetch", false, sanitizeError(error).message);
  }
}

function rankForPhotovoltaicProtocol(candidates) {
  return candidates
    .map((candidate, index) => {
      const bandGapScore = scoreBandGap(candidate.bandGapEv);
      const stabilityScore = scoreStability(candidate.energyAboveHullEv);
      const score = clamp(0.55 * stabilityScore + 0.45 * bandGapScore, 0.01, 0.99);
      return {
        ...candidate,
        rank: index + 1,
        score: Number(score.toFixed(3)),
        reasons: [
          `eHull=${candidate.energyAboveHullEv ?? "unknown"} eV`,
          `bandGap=${candidate.bandGapEv ?? "unknown"} eV`,
          `source=${candidate.source}`,
        ],
        domainEvidence: {
          preset: "dynamic-photovoltaic-absorber",
          score: Number(score.toFixed(3)),
          tier: candidate.source === "materials-project" ? "database-shortlist" : "dev-fixture-smoke",
          sourceLevel: candidate.source === "materials-project" ? "database-summary" : "smoke-fixture",
          missingProperties: [
            "absorptionCoefficientCm1",
            "directBandGapEv",
            "effectiveMassElectron",
            "effectiveMassHole",
            "defectToleranceScore",
            "literatureBaseline",
          ],
          nextCalculations: ["optical-absorption", "defect-transport", "phase-stability", "structure-validity"],
        },
      };
    })
    .sort((a, b) => b.score - a.score)
    .map((candidate, index) => ({ ...candidate, rank: index + 1 }));
}

function scoreBandGap(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return 0.2;
  }
  return clamp(1 - Math.abs(value - 1.4) / 1.4, 0, 1);
}

function scoreStability(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return 0.25;
  }
  return clamp(1 - value / 0.08, 0, 1);
}

function summarizePlan(result) {
  const plan = result.data.plan;
  return {
    summary: result.summary,
    manifestPath: result.data.manifestPath,
    reportPath: result.data.reportPath,
    protocolVersion: plan.protocolVersion,
    topic: plan.topic,
    selectedCandidateCount: plan.selectedCandidates.length,
    selectedCandidateIds: plan.selectedCandidates.map((candidate) => candidate.materialId),
    evidenceSchemaIds: plan.evidenceSchema.map((item) => item.id),
    calculationQueueCount: plan.calculationQueue.length,
    approvalGateCount: plan.approvalGates.length,
    claimPolicy: plan.claimPolicy,
  };
}

function summarizeExecution(result) {
  return {
    summary: result.summary,
    backend: result.data.backend,
    manifestPath: result.data.manifestPath,
    reportPath: result.data.reportPath,
    completedCalculations: result.data.completedCalculations,
    preparedCalculations: result.data.preparedCalculations,
    submittedCalculations: result.data.submittedCalculations,
    skippedCalculations: result.data.skippedCalculations,
    propertyUpdates: result.data.propertyUpdates ?? [],
    inputPathCount: result.data.inputPaths?.length ?? 0,
    resultPathCount: result.data.resultPaths?.length ?? 0,
    warnings: result.data.warnings ?? [],
  };
}

function recordArtifacts(paths) {
  for (const item of paths ?? []) {
    if (item) {
      artifactPaths.add(item);
    }
  }
}

async function validateArtifacts(paths) {
  const results = [];
  for (const item of paths) {
    try {
      const stat = await fs.stat(item);
      results.push({ path: item, exists: true, bytes: stat.size });
    } catch {
      results.push({ path: item, exists: false, bytes: 0 });
    }
  }
  return results;
}

function check(name, ok, detail) {
  checks.push({ name, ok: Boolean(ok), detail });
  if (!ok) {
    console.warn(`[check failed] ${name}: ${detail}`);
  }
}

function sanitizeError(error) {
  if (error instanceof Error) {
    return {
      name: error.name,
      message: error.message,
      code: error.code,
      hint: error.hint,
      details: error.details,
      stderr: error.stderr,
    };
  }
  return { message: String(error) };
}

function renderReport(summary) {
  const liveRows = summary.liveSearches
    .map((item) => `| ${item.label ?? "-"} | ${item.status} | ${item.candidateCount ?? 0} | ${item.usedOfflineData ?? "-"} |`)
    .join("\n");
  const checkRows = summary.checks
    .map((item) => `| ${item.ok ? "pass" : "fail"} | ${item.name} | ${String(item.detail ?? "").replaceAll("\n", " ")} |`)
    .join("\n");
  const artifactRows = summary.artifactsExist
    .slice(0, 40)
    .map((item) => `| ${item.exists ? "yes" : "no"} | ${relativeToRepo(item.path)} | ${item.bytes} |`)
    .join("\n");
  return [
    "# Live OpenClaw Dynamic Photovoltaic Protocol E2E",
    "",
    "## Verdict",
    "",
    `- Status: \`${summary.status}\``,
    `- Candidate source mode: \`${summary.candidateSourceMode}\``,
    `- Topic: ${summary.topic}`,
    `- Completed at: ${summary.completedAt}`,
    "",
    summary.verdict,
    "",
    "This run is an end-to-end software and workflow validation. It does not claim a new research-grade photovoltaic absorber discovery.",
    "",
    "## OpenClaw Path",
    "",
    `- Materials Lab configured: \`${summary.openclaw.materialsLabConfigured}\``,
    `- Materials Project API key configured: \`${summary.openclaw.materialsProjectApiKeyConfigured}\``,
    `- Python path: \`${summary.openclaw.pythonPath}\``,
    "",
    "## Live Search",
    "",
    "| Query | Status | Candidates | Offline data |",
    "| --- | --- | ---: | --- |",
    liveRows || "| - | skipped | 0 | - |",
    "",
    "## Protocol Compiler",
    "",
    `- Protocol-only selected candidates: ${summary.protocolOnly.selectedCandidateCount}`,
    `- Candidate-backed selected candidates: ${summary.candidateBackedPlan.selectedCandidateCount}`,
    `- Evidence schema: ${summary.candidateBackedPlan.evidenceSchemaIds.join(", ")}`,
    `- Approval gates: ${summary.candidateBackedPlan.approvalGateCount}`,
    "",
    "## Execution",
    "",
    `- dev-smoke completed calculations: ${summary.devSmoke.completedCalculations}`,
    `- dev-smoke property updates: ${summary.devSmoke.propertyUpdates.length}`,
    `- Quantum ESPRESSO prepared calculations: ${summary.quantumEspressoPrepare.preparedCalculations}`,
    `- Quantum ESPRESSO submitted calculations: ${summary.quantumEspressoPrepare.submittedCalculations}`,
    "",
    "## Checks",
    "",
    "| Result | Check | Detail |",
    "| --- | --- | --- |",
    checkRows,
    "",
    "## Artifacts",
    "",
    "| Exists | Path | Bytes |",
    "| --- | --- | ---: |",
    artifactRows,
    "",
  ].join("\n");
}

function relativeToRepo(item) {
  return path.relative(repoRoot, item) || ".";
}

function slugForPath(value) {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}
