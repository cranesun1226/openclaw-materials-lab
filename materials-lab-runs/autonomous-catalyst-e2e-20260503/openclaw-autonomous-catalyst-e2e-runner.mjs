import fs from "node:fs/promises";
import fsSync from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { resolveWorkspacePaths } from "../../dist/src/core/paths.js";
import { ArtifactService } from "../../dist/src/services/artifact-service.js";
import { PythonBridgeService } from "../../dist/src/services/python-bridge.js";

const repoRoot = path.resolve(path.join(path.dirname(fileURLToPath(import.meta.url)), "../.."));
const runRoot = path.join(repoRoot, "materials-lab-runs", "autonomous-catalyst-e2e-20260503");
const openclawConfigPath = path.join(os.homedir(), ".openclaw", "openclaw.json");
const startedAt = new Date().toISOString();
const topic = "Discover lead-free noble-metal-free oxygen evolution catalyst candidates for alkaline water splitting.";
const targetApplication = "alkaline oxygen evolution electrocatalyst";
const constraints = [
  "lead-free",
  "noble-metal-free",
  "alkaline-stable",
  "low-cost transition-metal chemistry preferred",
  "no research-grade claim without parsed evidence",
];
const checks = [];
const artifactPaths = new Set();

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

  const planResult = await bridge.planResearchLoop({
    artifactDir: path.join(paths.reportsDir, "autonomous-catalyst-plan"),
    researchGoal: topic,
    targetApplication,
    constraints,
    candidateGeneration: {
      autoDiscover: true,
      strategy: "search live database candidates from transition-metal oxide/sulfide catalyst families before ranking",
      elementsExclude: ["Pb", "Cd", "Hg", "Pt", "Ir", "Ru", "Rh", "Pd"],
      maxQueries: 6,
      perQueryLimit: 10,
      searchPayloads: [
        { elementsAll: ["Fe", "O"], maxEnergyAboveHullEv: 0.08, minBandGapEv: 0, maxBandGapEv: 6, limit: 10 },
        { elementsAll: ["Co", "O"], maxEnergyAboveHullEv: 0.08, minBandGapEv: 0, maxBandGapEv: 6, limit: 10 },
        { elementsAll: ["Ni", "O"], maxEnergyAboveHullEv: 0.08, minBandGapEv: 0, maxBandGapEv: 6, limit: 10 },
        { elementsAll: ["Mn", "O"], maxEnergyAboveHullEv: 0.08, minBandGapEv: 0, maxBandGapEv: 6, limit: 10 },
        { elementsAll: ["Mo", "S"], maxEnergyAboveHullEv: 0.08, minBandGapEv: 0, maxBandGapEv: 6, limit: 10 },
      ],
    },
    validationMethods: ["database", "literature", "dft", "experiment"],
    budget: {
      maxCandidates: 3,
      maxCalculations: 16,
      maxWallTimeHours: 96,
      maxLoopIterations: 2,
      allowExpensiveCalculations: false,
    },
    autonomyMode: "high-autonomy-plan",
    approvalPolicy: "approval-required",
  });
  recordArtifacts(planResult.artifacts);

  const plan = planResult.data.plan;
  const selected = plan.selectedCandidates ?? [];
  const evidenceIds = (plan.evidenceSchema ?? []).map((item) => item.id);
  const discovery = plan.autonomousDiscovery ?? {};
  const claimStatus = plan.claimStatus ?? {};

  check("protocol-version", plan.protocolVersion === "dynamic-research-protocol-v1", plan.protocolVersion);
  check("topic-inference", plan.topic?.id === "catalyst", JSON.stringify(plan.topic));
  check("autonomous-discovery-enabled", discovery.enabled === true, JSON.stringify(discovery));
  check("autonomous-discovery-completed", discovery.status === "completed", JSON.stringify(discovery));
  check("live-source-mode", discovery.sourceMode === "materials-project-live", discovery.sourceMode);
  check("candidate-pool-nonempty", selected.length > 0, `selected=${selected.length}`);
  check("surface-activity-schema", evidenceIds.includes("surface-activity"), evidenceIds.join(", "));
  check("operando-stability-schema", evidenceIds.includes("operando-stability"), evidenceIds.join(", "));
  check("claim-locked", claimStatus.researchGradeClaimAllowed === false, JSON.stringify(claimStatus));
  check("candidate-pool-artifact", Boolean(planResult.data.candidatePoolPath), planResult.data.candidatePoolPath);
  check("evidence-ledger-artifact", Boolean(planResult.data.evidenceLedgerPath), planResult.data.evidenceLedgerPath);
  check("excluded-elements-filtered", selected.every((candidate) => !hasExcludedElement(candidate)), selected.map((candidate) => candidate.materialId).join(", "));

  const topCandidate = selected[0];
  const structureResult = await bridge.fetchStructure({
    materialId: topCandidate.materialId,
    format: "both",
    artifactDir: path.join(paths.structuresDir, topCandidate.materialId),
    allowOffline: false,
  });
  recordArtifacts(structureResult.artifacts);
  check("live-structure-fetch", structureResult.data.usedOfflineData === false, structureResult.summary);

  const devSmoke = await bridge.executeResearchPlan({
    planPath: planResult.data.manifestPath,
    artifactDir: path.join(paths.reportsDir, "autonomous-catalyst-dev-smoke"),
    backend: "dev-smoke",
    allowBlockedDevSmoke: true,
    maxSteps: 10,
  });
  recordArtifacts(devSmoke.artifacts);
  recordArtifacts(devSmoke.data.resultPaths);
  check("dev-smoke-completed", devSmoke.data.completedCalculations > 0, devSmoke.summary);
  check("dev-smoke-no-property-updates", (devSmoke.data.propertyUpdates ?? []).length === 0, "propertyUpdates=0");

  const qePrepare = await bridge.executeResearchPlan({
    planPath: planResult.data.manifestPath,
    artifactDir: path.join(paths.reportsDir, "autonomous-catalyst-qe-prepare"),
    backend: "quantum-espresso",
    executionMode: "prepare",
    allowExecution: false,
    maxSteps: 16,
    backendConfig: {
      pseudoDir: "./pseudo",
      kpoints: "2 2 2 0 0 0",
    },
  });
  recordArtifacts(qePrepare.artifacts);
  recordArtifacts(qePrepare.data.resultPaths);
  recordArtifacts(qePrepare.data.inputPaths);
  check("qe-prepared", qePrepare.data.preparedCalculations > 0, qePrepare.summary);
  check("qe-not-submitted", qePrepare.data.submittedCalculations === 0, "submittedCalculations=0");
  const scfInputPath = (qePrepare.data.inputPaths ?? []).find((item) => item.endsWith("pw.scf.in"));
  const scfInput = scfInputPath ? await fs.readFile(scfInputPath, "utf8") : "";
  check("qe-scf-input", scfInput.includes("ATOMIC_SPECIES") && scfInput.includes("K_POINTS automatic"), scfInputPath ?? "no pw.scf.in");

  const candidatePoolText = await fs.readFile(planResult.data.candidatePoolPath, "utf8");
  const evidenceLedgerText = await fs.readFile(planResult.data.evidenceLedgerPath, "utf8");
  check("candidate-pool-live", candidatePoolText.includes("materials-project"), planResult.data.candidatePoolPath);
  check("ledger-blocks-research-grade", evidenceLedgerText.includes("blocks-research-grade-claim"), planResult.data.evidenceLedgerPath);

  const summary = {
    status: checks.every((item) => item.ok) ? "passed" : "failed",
    startedAt,
    completedAt: new Date().toISOString(),
    runRoot,
    topic,
    targetApplication,
    constraints,
    openclaw: {
      materialsLabConfigured: Boolean(openclawConfig.plugins?.entries?.["materials-lab"]),
      materialsProjectApiKeyConfigured: Boolean(pluginConfig.mpApiKey),
      pythonPath: config.pythonPath,
    },
    plan: summarizePlan(planResult),
    discovery,
    selectedCandidates: selected,
    structure: {
      materialId: topCandidate.materialId,
      summary: structureResult.summary,
      usedOfflineData: structureResult.data.usedOfflineData,
      structurePath: structureResult.data.structurePath,
      cifPath: structureResult.data.cifPath,
    },
    devSmoke: summarizeExecution(devSmoke),
    quantumEspressoPrepare: summarizeExecution(qePrepare),
    checks,
    artifactPaths: [...artifactPaths].sort(),
    artifactsExist: await validateArtifacts([...artifactPaths]),
    verdict:
      "OpenClaw Materials Lab autonomously compiled a catalyst research protocol from a topic, discovered live Materials Project candidates, wrote evidence artifacts, and prepared backend inputs without making research-grade claims.",
  };
  const summaryPath = path.join(paths.reportsDir, "openclaw-autonomous-catalyst-e2e-summary.json");
  const reportPath = path.join(paths.reportsDir, "openclaw-autonomous-catalyst-e2e-process.md");
  await fs.writeFile(summaryPath, JSON.stringify(summary, null, 2) + "\n", "utf8");
  await fs.writeFile(reportPath, renderReport(summary), "utf8");
  console.log(JSON.stringify({ status: summary.status, summaryPath, reportPath }, null, 2));
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
  };
  const failurePath = path.join(paths.reportsDir, "openclaw-autonomous-catalyst-e2e-failure.json");
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

function summarizePlan(result) {
  const plan = result.data.plan;
  return {
    summary: result.summary,
    manifestPath: result.data.manifestPath,
    reportPath: result.data.reportPath,
    queryLogPath: result.data.queryLogPath,
    candidatePoolPath: result.data.candidatePoolPath,
    evidenceLedgerPath: result.data.evidenceLedgerPath,
    topic: plan.topic,
    selectedCandidateIds: (plan.selectedCandidates ?? []).map((candidate) => candidate.materialId),
    evidenceSchemaIds: (plan.evidenceSchema ?? []).map((item) => item.id),
    calculationQueueCount: plan.calculationQueue?.length ?? 0,
    approvalGateCount: plan.approvalGates?.length ?? 0,
    claimStatus: plan.claimStatus,
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

function hasExcludedElement(candidate) {
  const excluded = new Set(["Pb", "Cd", "Hg", "Pt", "Ir", "Ru", "Rh", "Pd"]);
  return (candidate.elements ?? []).some((element) => excluded.has(element));
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
  const checks = summary.checks
    .map((item) => `| ${item.ok ? "pass" : "fail"} | ${item.name} | ${String(item.detail ?? "").replaceAll("\n", " ")} |`)
    .join("\n");
  const candidates = summary.selectedCandidates
    .map((candidate) => `| ${candidate.rank ?? "-"} | ${candidate.materialId} | ${candidate.formula} | ${candidate.source} | ${candidate.score ?? "-"} | ${candidate.evidenceTier ?? "-"} |`)
    .join("\n");
  const artifacts = summary.artifactsExist
    .slice(0, 50)
    .map((item) => `| ${item.exists ? "yes" : "no"} | ${path.relative(repoRoot, item.path)} | ${item.bytes} |`)
    .join("\n");
  return [
    "# OpenClaw Autonomous Catalyst E2E",
    "",
    "## Verdict",
    "",
    `- Status: \`${summary.status}\``,
    `- Topic: ${summary.topic}`,
    `- Completed at: ${summary.completedAt}`,
    "",
    summary.verdict,
    "",
    "This is a workflow validation, not a research-grade catalyst discovery claim.",
    "",
    "## Discovery",
    "",
    `- Status: \`${summary.discovery.status}\``,
    `- Source mode: \`${summary.discovery.sourceMode}\``,
    `- Queries: ${summary.discovery.successfulQueryCount} / ${summary.discovery.queryCount}`,
    `- Ranked candidates: ${summary.discovery.rankedCandidateCount}`,
    `- Candidate pool: ${path.relative(repoRoot, summary.plan.candidatePoolPath)}`,
    `- Evidence ledger: ${path.relative(repoRoot, summary.plan.evidenceLedgerPath)}`,
    "",
    "## Selected Candidates",
    "",
    "| Rank | Material | Formula | Source | Score | Evidence Tier |",
    "| ---: | --- | --- | --- | ---: | --- |",
    candidates || "| - | - | - | - | - | - |",
    "",
    "## Protocol",
    "",
    `- Evidence schema: ${summary.plan.evidenceSchemaIds.join(", ")}`,
    `- Queue steps: ${summary.plan.calculationQueueCount}`,
    `- Approval gates: ${summary.plan.approvalGateCount}`,
    `- Research-grade claim allowed: \`${summary.plan.claimStatus?.researchGradeClaimAllowed}\``,
    "",
    "## Execution",
    "",
    `- Structure fetched: ${path.relative(repoRoot, summary.structure.structurePath)}`,
    `- dev-smoke completed: ${summary.devSmoke.completedCalculations}`,
    `- dev-smoke property updates: ${summary.devSmoke.propertyUpdates.length}`,
    `- Quantum ESPRESSO prepared: ${summary.quantumEspressoPrepare.preparedCalculations}`,
    `- Quantum ESPRESSO submitted: ${summary.quantumEspressoPrepare.submittedCalculations}`,
    "",
    "## Checks",
    "",
    "| Result | Check | Detail |",
    "| --- | --- | --- |",
    checks,
    "",
    "## Artifacts",
    "",
    "| Exists | Path | Bytes |",
    "| --- | --- | ---: |",
    artifacts,
    "",
  ].join("\n");
}
