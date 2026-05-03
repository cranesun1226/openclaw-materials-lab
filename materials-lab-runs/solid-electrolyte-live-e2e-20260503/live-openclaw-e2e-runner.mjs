import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { resolveWorkspacePaths } from "../../dist/src/core/paths.js";
import { PythonBridgeService } from "../../dist/src/services/python-bridge.js";
import { ArtifactService } from "../../dist/src/services/artifact-service.js";
import { NoteService } from "../../dist/src/services/note-service.js";

const repoRoot = path.resolve(new URL("../..", import.meta.url).pathname);
const runRoot = path.join(repoRoot, "materials-lab-runs", "solid-electrolyte-live-e2e-20260503");
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
    label: "Li-La-Zr-O garnet electrolyte family",
    payload: {
      elementsAll: ["Li", "La", "Zr", "O"],
      maxEnergyAboveHullEv: 0.1,
      minBandGapEv: 2.0,
      maxBandGapEv: 8.5,
      limit: 10,
      allowOffline: false,
    },
  },
  {
    label: "Li-P-S thiophosphate electrolyte family",
    payload: {
      elementsAll: ["Li", "P", "S"],
      maxEnergyAboveHullEv: 0.1,
      minBandGapEv: 2.0,
      maxBandGapEv: 8.5,
      limit: 10,
      allowOffline: false,
    },
  },
  {
    label: "Li-Ge-P-S LGPS-like electrolyte family",
    payload: {
      elementsAll: ["Li", "Ge", "P", "S"],
      maxEnergyAboveHullEv: 0.1,
      minBandGapEv: 2.0,
      maxBandGapEv: 8.5,
      limit: 10,
      allowOffline: false,
    },
  },
  {
    label: "Li-Al-Ti-P-O NASICON-like electrolyte family",
    payload: {
      elementsAll: ["Li", "Al", "Ti", "P", "O"],
      maxEnergyAboveHullEv: 0.1,
      minBandGapEv: 2.0,
      maxBandGapEv: 8.5,
      limit: 10,
      allowOffline: false,
    },
  },
  {
    label: "Li-Zr-P-O phosphate electrolyte family",
    payload: {
      elementsAll: ["Li", "Zr", "P", "O"],
      maxEnergyAboveHullEv: 0.1,
      minBandGapEv: 2.0,
      maxBandGapEv: 8.5,
      limit: 10,
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
  if (result.data.usedOfflineData) {
    throw new Error(`Live Materials Project validation failed: ${query.label} used offline data.`);
  }
  for (const candidate of candidates) {
    if (candidate?.materialId && !candidateById.has(candidate.materialId)) {
      candidateById.set(candidate.materialId, candidate);
    }
  }
}

const candidates = [...candidateById.values()];
if (candidates.length < 3) {
  throw new Error(`Expected at least 3 live candidates, got ${candidates.length}.`);
}

const compareDir = path.join(paths.plotsDir, "solid-electrolyte-ranking");
const comparison = await bridge.compareCandidates({
  candidates,
  criteria: {
    stabilityWeight: 0.50,
    bandGapWeight: 0.35,
    densityWeight: 0.15,
    bandGapTargetEv: 5.0,
    densityTargetGcm3: 3.0,
  },
  topK: Math.min(10, candidates.length),
  artifactDir: compareDir,
});

const ranked = comparison.data.ranked ?? [];
const structureRuns = [];
const structureFailures = [];
const artifactPaths = [...(comparison.artifacts ?? [])];

for (const candidate of ranked.slice(0, Math.min(8, ranked.length))) {
  if (structureRuns.length >= 3) {
    break;
  }
  const structureDir = path.join(paths.structuresDir, slugForPath(candidate.materialId));
  try {
    const fetched = await bridge.fetchStructure({
      materialId: candidate.materialId,
      format: "both",
      artifactDir: structureDir,
      allowOffline: false,
    });
    if (fetched.data.usedOfflineData) {
      throw new Error("fetchStructure used offline data");
    }
    artifactPaths.push(...(fetched.artifacts ?? []));

    const analysis = await bridge.analyzeStructure({
      materialId: candidate.materialId,
      structurePath: fetched.data.structurePath,
      artifactDir: structureDir,
      allowOffline: false,
    });
    if (analysis.data.usedOfflineData) {
      throw new Error("analyzeStructure used offline data");
    }
    artifactPaths.push(...(analysis.artifacts ?? []));

    structureRuns.push({
      materialId: candidate.materialId,
      formula: candidate.formula,
      fetchSummary: fetched.summary,
      analysisSummary: analysis.summary,
      structurePath: fetched.data.structurePath,
      cifPath: fetched.data.cifPath,
      plotPath: analysis.data.plotPath,
      usedOfflineData: false,
    });
  } catch (error) {
    structureFailures.push({
      materialId: candidate.materialId,
      formula: candidate.formula,
      error: error instanceof Error ? error.message : String(error),
    });
  }
}

if (structureRuns.length < 3) {
  throw new Error(`Expected at least 3 live structure analyses, got ${structureRuns.length}.`);
}

const note = await noteService.saveNote({
  title: "Live Materials Project solid-state electrolyte screening process",
  noteType: "process",
  tags: ["materials-project", "solid-electrolyte", "battery", "openclaw-e2e"],
  candidateIds: ranked.map((candidate) => candidate.materialId),
  artifactPaths,
  body: [
    "Question: Which stable lithium-containing inorganic materials from Materials Project are promising proxy candidates for solid-state battery electrolyte exploration?",
    "",
    "Process:",
    "1. Queried Materials Project live data for garnet, thiophosphate, LGPS-like, NASICON-like, and phosphate electrolyte families.",
    "2. Disabled offline fallback in every query and structure fetch.",
    "3. Merged duplicate material ids across searches.",
    "4. Ranked candidates using weighted stability, high band-gap alignment, and density alignment.",
    "5. Fetched JSON/CIF structures for the top candidates that had retrievable structures.",
    "6. Ran pymatgen-based structure analysis and generated metric plots.",
    "7. Exported a markdown report plus a machine-readable validation summary.",
  ].join("\n"),
});

const report = await bridge.exportReport({
  title: "Live Materials Project Solid-State Electrolyte Candidate Screening",
  goal:
    "Use OpenClaw Materials Lab with a live Materials Project API key to shortlist stable lithium-containing inorganic candidates for solid-state battery electrolyte exploration.",
  evaluationCriteria: [
    "Live Materials Project source only; offline fallback disabled.",
    "Energy above hull <= 0.1 eV for preliminary stability screening.",
    "Band gap between 2.0 and 8.5 eV, ranked toward a 5.0 eV target as an electronic-insulation proxy.",
    "Density alignment toward 3.0 g/cm3 as a lightweight proxy for inorganic solid electrolyte families.",
    "Top candidates must have retrievable structures for downstream analysis.",
    "This demo does not compute Li-ion conductivity, migration barriers, or electrochemical stability windows.",
  ],
  rankedCandidates: ranked,
  notePaths: [note.path],
  artifactPaths,
  outputPath: path.join(paths.reportsDir, "live-solid-electrolyte-e2e-report.md"),
});

const validation = {
  usedOfflineDataAnywhere:
    searches.some((search) => search.usedOfflineData) ||
    structureRuns.some((run) => run.usedOfflineData),
  searchFamilies: searches.length,
  totalUniqueCandidates: candidates.length,
  rankedCandidates: ranked.length,
  structuresAnalyzed: structureRuns.length,
  requiredArtifactsExist: await validateArtifacts([
    ...(comparison.artifacts ?? []),
    ...structureRuns.flatMap((run) => [run.structurePath, run.cifPath, run.plotPath].filter(Boolean)),
    report.data.outputPath,
    note.path,
  ]),
};

const summary = {
  generatedAt: new Date().toISOString(),
  runRoot,
  topic: "solid-state lithium battery electrolyte screening",
  liveMaterialsProject: true,
  searches,
  totalUniqueCandidates: candidates.length,
  rankedCandidates: ranked,
  structuresAnalyzed: structureRuns,
  structureFailures,
  notePath: note.path,
  reportPath: report.data.outputPath,
  artifactPaths,
  validation,
};

const summaryPath = path.join(paths.reportsDir, "live-solid-electrolyte-e2e-summary.json");
await fs.writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");

const processReportPath = path.join(paths.reportsDir, "live-openclaw-solid-electrolyte-e2e-process.md");
await fs.writeFile(
  processReportPath,
  [
    "# Live OpenClaw Materials Lab Solid Electrolyte E2E Process",
    "",
    `Generated: ${summary.generatedAt}`,
    "",
    "## Question",
    "",
    "Which stable lithium-containing inorganic Materials Project candidates are worth shortlisting for solid-state battery electrolyte exploration?",
    "",
    "## Process",
    "",
    "- Used the real OpenClaw `materials-lab` configuration and Python worker.",
    "- Read the Materials Project API key from `~/.openclaw/openclaw.json` without printing it.",
    "- Disabled offline fallback in every live MP query and structure fetch.",
    "- Queried garnet, thiophosphate, LGPS-like, NASICON-like, and phosphate electrolyte families.",
    "- Ranked candidates with stability, high band-gap alignment, and density alignment.",
    "- Fetched and analyzed structures for the top ranked candidates.",
    "- Exported the final markdown report and machine-readable JSON summary.",
    "",
    "## Validation",
    "",
    `- Offline fallback used anywhere: ${validation.usedOfflineDataAnywhere}`,
    `- Search families: ${validation.searchFamilies}`,
    `- Unique live candidates: ${validation.totalUniqueCandidates}`,
    `- Ranked candidates: ${validation.rankedCandidates}`,
    `- Structures analyzed: ${validation.structuresAnalyzed}`,
    `- Required artifacts exist: ${validation.requiredArtifactsExist.ok}`,
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
    "## Structure Fetch Failures",
    "",
    ...(structureFailures.length
      ? structureFailures.map((failure) => `- ${failure.materialId} (${failure.formula}): ${failure.error}`)
      : ["- None"]),
    "",
  ].join("\n"),
  "utf8",
);

console.log(
  JSON.stringify(
    {
      ok: true,
      topic: summary.topic,
      runRoot,
      reportPath: report.data.outputPath,
      summaryPath,
      processReportPath,
      validation,
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

async function validateArtifacts(pathsToCheck) {
  const missing = [];
  for (const item of pathsToCheck) {
    try {
      const stat = await fs.stat(item);
      if (!stat.isFile() || stat.size <= 0) {
        missing.push(item);
      }
    } catch {
      missing.push(item);
    }
  }
  return {
    ok: missing.length === 0,
    checked: pathsToCheck.length,
    missing,
  };
}

function slugForPath(value) {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64);
}
