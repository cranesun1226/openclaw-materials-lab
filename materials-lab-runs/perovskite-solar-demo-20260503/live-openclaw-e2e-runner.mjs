import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { resolveWorkspacePaths } from "../../dist/src/core/paths.js";
import { PythonBridgeService } from "../../dist/src/services/python-bridge.js";
import { ArtifactService } from "../../dist/src/services/artifact-service.js";
import { NoteService } from "../../dist/src/services/note-service.js";

const repoRoot = path.resolve(new URL("../..", import.meta.url).pathname);
const runRoot = path.join(repoRoot, "materials-lab-runs", "perovskite-solar-live-e2e-20260503");
const openclawConfigPath = path.join(os.homedir(), ".openclaw", "openclaw.json");

const configText = await fs.readFile(openclawConfigPath, "utf8");
const openclawConfig = JSON.parse(configText);
const pluginConfig = openclawConfig.plugins?.entries?.["materials-lab"]?.config ?? {};

if (!pluginConfig.mpApiKey) {
  throw new Error("Materials Project API key is not configured in OpenClaw.");
}

const config = {
  pythonPath: pluginConfig.pythonPath,
  mpApiKey: pluginConfig.mpApiKey,
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
const noteService = new NoteService(artifactService);
const bridge = new PythonBridgeService(config, paths, logger);

await artifactService.ensureReady();

const searchQueries = [
  {
    label: "Sr-Ti-O oxide perovskite family",
    payload: {
      elementsAll: ["Sr", "Ti", "O"],
      maxEnergyAboveHullEv: 0.05,
      minBandGapEv: 1.0,
      maxBandGapEv: 4.2,
      limit: 8,
      allowOffline: false,
    },
  },
  {
    label: "Ba-Ti-O oxide perovskite family",
    payload: {
      elementsAll: ["Ba", "Ti", "O"],
      maxEnergyAboveHullEv: 0.05,
      minBandGapEv: 1.0,
      maxBandGapEv: 4.2,
      limit: 8,
      allowOffline: false,
    },
  },
  {
    label: "Ca-Ti-O oxide perovskite family",
    payload: {
      elementsAll: ["Ca", "Ti", "O"],
      maxEnergyAboveHullEv: 0.05,
      minBandGapEv: 1.0,
      maxBandGapEv: 4.2,
      limit: 8,
      allowOffline: false,
    },
  },
  {
    label: "Na-Nb-O oxide perovskite family",
    payload: {
      elementsAll: ["Na", "Nb", "O"],
      maxEnergyAboveHullEv: 0.05,
      minBandGapEv: 1.0,
      maxBandGapEv: 4.2,
      limit: 8,
      allowOffline: false,
    },
  },
];

const searches = [];
const candidateById = new Map();

for (const query of searchQueries) {
  const result = await bridge.searchMaterials(query.payload);
  const candidates = result.data.candidates ?? [];
  searches.push({
    label: query.label,
    summary: result.summary,
    usedOfflineData: result.data.usedOfflineData,
    candidateCount: candidates.length,
    candidateIds: candidates.map((candidate) => candidate.materialId),
  });
  for (const candidate of candidates) {
    if (candidate?.materialId && !candidateById.has(candidate.materialId)) {
      candidateById.set(candidate.materialId, candidate);
    }
  }
}

const candidates = [...candidateById.values()];
if (candidates.length < 2) {
  throw new Error(`Expected at least 2 live candidates, got ${candidates.length}.`);
}

const compareDir = path.join(paths.plotsDir, "live-candidate-ranking");
const comparison = await bridge.compareCandidates({
  candidates,
  criteria: {
    stabilityWeight: 0.45,
    bandGapWeight: 0.40,
    densityWeight: 0.15,
    bandGapTargetEv: 2.8,
    densityTargetGcm3: 5.0,
  },
  topK: Math.min(8, candidates.length),
  artifactDir: compareDir,
});

const ranked = comparison.data.ranked ?? [];
const topForStructure = ranked.slice(0, Math.min(3, ranked.length));
const structureRuns = [];
const artifactPaths = [...(comparison.artifacts ?? [])];

for (const candidate of topForStructure) {
  const structureDir = path.join(paths.structuresDir, slugForPath(candidate.materialId));
  const fetched = await bridge.fetchStructure({
    materialId: candidate.materialId,
    format: "both",
    artifactDir: structureDir,
    allowOffline: false,
  });
  artifactPaths.push(...(fetched.artifacts ?? []));

  const analysis = await bridge.analyzeStructure({
    materialId: candidate.materialId,
    structurePath: fetched.data.structurePath,
    artifactDir: structureDir,
    allowOffline: false,
  });
  artifactPaths.push(...(analysis.artifacts ?? []));

  structureRuns.push({
    materialId: candidate.materialId,
    formula: candidate.formula,
    fetchSummary: fetched.summary,
    analysisSummary: analysis.summary,
    structurePath: fetched.data.structurePath,
    cifPath: fetched.data.cifPath,
    plotPath: analysis.data.plotPath,
    usedOfflineData: fetched.data.usedOfflineData || analysis.data.usedOfflineData,
  });
}

const note = await noteService.saveNote({
  title: "Live Materials Project perovskite solar screening process",
  noteType: "process",
  tags: ["materials-project", "perovskite", "solar", "openclaw-e2e"],
  candidateIds: ranked.map((candidate) => candidate.materialId),
  artifactPaths,
  body: [
    "Question: Which stable oxide perovskite-family candidates from Materials Project have band gaps near the target range for perovskite solar-material exploration?",
    "",
    "Process:",
    "1. Queried Materials Project live data for Sr-Ti-O, Ba-Ti-O, Ca-Ti-O, and Na-Nb-O oxide families with hull energy <= 0.05 eV and 1.0-4.2 eV band gaps.",
    "2. Merged duplicate material ids across searches.",
    "3. Ranked candidates using weighted stability, band-gap alignment, and density alignment.",
    "4. Fetched structures for the top candidates and generated JSON/CIF artifacts.",
    "5. Ran pymatgen-based structure analysis and generated metric plots.",
    "6. Exported a markdown report with candidate ranking and artifact references.",
  ].join("\n"),
});

const report = await bridge.exportReport({
  title: "Live Materials Project Perovskite Solar Candidate Screening",
  goal:
    "Use OpenClaw Materials Lab with a live Materials Project API key to identify stable oxide perovskite-family candidates relevant to solar-material exploration.",
  evaluationCriteria: [
    "Live Materials Project source only; offline fallback disabled.",
    "Energy above hull <= 0.05 eV for stability screening.",
    "Band gap between 1.0 and 4.2 eV, ranked toward a 2.8 eV target for this oxide-perovskite demo.",
    "Density alignment toward 5.0 g/cm3 as a lightweight proxy for compact inorganic oxide structures.",
    "Top candidates must have retrievable structures for downstream analysis.",
  ],
  rankedCandidates: ranked,
  notePaths: [note.path],
  artifactPaths,
  outputPath: path.join(paths.reportsDir, "live-perovskite-solar-e2e-report.md"),
});

const summary = {
  generatedAt: new Date().toISOString(),
  runRoot,
  liveMaterialsProject: true,
  searches,
  totalUniqueCandidates: candidates.length,
  rankedCandidates: ranked,
  structuresAnalyzed: structureRuns,
  notePath: note.path,
  reportPath: report.data.outputPath,
  artifactPaths,
};

const summaryPath = path.join(paths.reportsDir, "live-perovskite-solar-e2e-summary.json");
await fs.writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");

const processReportPath = path.join(paths.reportsDir, "live-openclaw-e2e-process.md");
await fs.writeFile(
  processReportPath,
  [
    "# Live OpenClaw Materials Lab E2E Process",
    "",
    `Generated: ${summary.generatedAt}`,
    "",
    "## Question",
    "",
    "Which stable oxide perovskite-family candidates from Materials Project are worth shortlisting for perovskite solar-material exploration?",
    "",
    "## Process",
    "",
    "- Used the real OpenClaw `materials-lab` configuration and Python worker.",
    "- Read the Materials Project API key from `~/.openclaw/openclaw.json` without printing it.",
    "- Disabled offline fallback in every live MP query.",
    "- Queried Sr-Ti-O, Ba-Ti-O, Ca-Ti-O, and Na-Nb-O families.",
    "- Ranked candidates with stability, band-gap alignment, and density alignment.",
    "- Fetched and analyzed structures for the top ranked candidates.",
    "- Exported the final markdown report and machine-readable JSON summary.",
    "",
    "## Outputs",
    "",
    `- Summary JSON: ${summaryPath}`,
    `- Final report: ${report.data.outputPath}`,
    `- Process note: ${note.path}`,
    `- Ranking plot/artifacts: ${artifactPaths.join(", ")}`,
    "",
    "## Top Candidates",
    "",
    ...ranked.map(
      (candidate) =>
        `- ${candidate.rank}. ${candidate.materialId} (${candidate.formula}) score=${candidate.score}, bandGap=${candidate.bandGapEv}, eHull=${candidate.energyAboveHullEv}`,
    ),
    "",
  ].join("\n"),
  "utf8",
);

console.log(
  JSON.stringify(
    {
      ok: true,
      runRoot,
      reportPath: report.data.outputPath,
      summaryPath,
      processReportPath,
      topCandidates: ranked.slice(0, 5).map((candidate) => ({
        rank: candidate.rank,
        materialId: candidate.materialId,
        formula: candidate.formula,
        score: candidate.score,
        bandGapEv: candidate.bandGapEv,
        energyAboveHullEv: candidate.energyAboveHullEv,
      })),
    },
    null,
    2,
  ),
);

function slugForPath(value) {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64);
}
