import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { resolveWorkspacePaths } from "../../dist/src/core/paths.js";
import { PythonBridgeService } from "../../dist/src/services/python-bridge.js";
import { ArtifactService } from "../../dist/src/services/artifact-service.js";
import { NoteService } from "../../dist/src/services/note-service.js";

const repoRoot = path.resolve(new URL("../..", import.meta.url).pathname);
const runRoot = path.join(repoRoot, "materials-lab-runs", "solid-electrolyte-live-e2e-v2-20260503");
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
    label: "LLZO garnet oxide",
    payload: {
      elementsAll: ["Li", "La", "Zr", "O"],
      maxEnergyAboveHullEv: 0.1,
      minBandGapEv: 2.0,
      maxBandGapEv: 8.5,
      limit: 20,
      allowOffline: false,
    },
  },
  {
    label: "Thiophosphate sulfide",
    payload: {
      elementsAll: ["Li", "P", "S"],
      maxEnergyAboveHullEv: 0.1,
      minBandGapEv: 1.5,
      maxBandGapEv: 8.5,
      limit: 20,
      allowOffline: false,
    },
  },
  {
    label: "LGPS-like sulfide",
    payload: {
      elementsAll: ["Li", "Ge", "P", "S"],
      maxEnergyAboveHullEv: 0.1,
      minBandGapEv: 1.5,
      maxBandGapEv: 8.5,
      limit: 20,
      allowOffline: false,
    },
  },
  {
    label: "NASICON LATP-like oxide",
    payload: {
      elementsAll: ["Li", "Al", "Ti", "P", "O"],
      maxEnergyAboveHullEv: 0.1,
      minBandGapEv: 2.0,
      maxBandGapEv: 8.5,
      limit: 20,
      allowOffline: false,
    },
  },
  {
    label: "Zirconium phosphate oxide",
    payload: {
      elementsAll: ["Li", "Zr", "P", "O"],
      maxEnergyAboveHullEv: 0.1,
      minBandGapEv: 2.0,
      maxBandGapEv: 8.5,
      limit: 20,
      allowOffline: false,
    },
  },
  {
    label: "Argyrodite-like chloride sulfide",
    payload: {
      elementsAll: ["Li", "P", "S", "Cl"],
      maxEnergyAboveHullEv: 0.1,
      minBandGapEv: 1.5,
      maxBandGapEv: 8.5,
      limit: 20,
      allowOffline: false,
    },
  },
  {
    label: "Chloride halide electrolyte",
    payload: {
      elementsAll: ["Li", "Y", "Cl"],
      maxEnergyAboveHullEv: 0.1,
      minBandGapEv: 2.0,
      maxBandGapEv: 8.5,
      limit: 20,
      allowOffline: false,
    },
  },
  {
    label: "Antiperovskite oxyhalide",
    payload: {
      elementsAll: ["Li", "O", "Cl"],
      maxEnergyAboveHullEv: 0.1,
      minBandGapEv: 2.0,
      maxBandGapEv: 8.5,
      limit: 20,
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
    payload: query.payload,
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

const compareDir = path.join(paths.plotsDir, "solid-electrolyte-ranking-v2");
const comparison = await bridge.compareCandidates({
  candidates,
  criteria: {
    preset: "solid-electrolyte",
    screeningLevel: "proxy-screen",
    bandGapScoringMode: "minimum",
    minimumBandGapEv: 2.0,
    densityScoringMode: "advisory",
    densityWeight: 0.0,
    diversifyBy: "formula",
    maxPerFormula: 1,
    maxPerFamily: 3,
  },
  topK: Math.min(12, candidates.length),
  artifactDir: compareDir,
});

const ranked = comparison.data.ranked ?? [];
if (ranked.length < 3) {
  throw new Error(`Expected at least 3 ranked candidates after diversity controls, got ${ranked.length}.`);
}

const structureRuns = [];
const structureFailures = [];
const artifactPaths = [...(comparison.artifacts ?? [])];

for (const candidate of ranked.slice(0, Math.min(8, ranked.length))) {
  if (structureRuns.length >= 4) {
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
      family: candidate.family,
      fetchSummary: fetched.summary,
      analysisSummary: analysis.summary,
      summaryMetrics: analysis.data.summaryMetrics,
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
  title: "Live Materials Project solid-state electrolyte screening v2 process",
  noteType: "process",
  tags: ["materials-project", "solid-electrolyte", "battery", "openclaw-e2e", "diversity", "proxy-screen"],
  candidateIds: ranked.map((candidate) => candidate.materialId),
  artifactPaths,
  body: [
    "Question: Can the patched Materials Lab solid-electrolyte preset produce a more defensible live proxy shortlist than the first E2E run?",
    "",
    "Process:",
    "1. Queried live Materials Project data across oxide, sulfide, halide, oxyhalide, NASICON-like, LGPS-like, and phosphate electrolyte families.",
    "2. Disabled offline fallback in every live MP query and structure fetch.",
    "3. Merged duplicate material ids across searches.",
    "4. Ranked candidates with the new solid-electrolyte preset: stability gate, minimum band-gap screen, density advisory, and formula/family diversity controls.",
    "5. Exported score component plot plus CSV/JSONL ranking tables.",
    "6. Fetched JSON/CIF structures for diverse top candidates.",
    "7. Ran pymatgen-based structure analysis with Li sublattice proxy descriptors and unit-aware metric plots.",
    "8. Exported an enhanced markdown report plus a machine-readable validation summary.",
  ].join("\n"),
});

const report = await bridge.exportReport({
  title: "Live Materials Project Solid-State Electrolyte Candidate Screening V2",
  goal:
    "Validate the patched OpenClaw Materials Lab solid-electrolyte preset on live Materials Project data and check whether it produces a more diverse, better-labeled proxy shortlist.",
  evaluationCriteria: [
    "Live Materials Project source only; offline fallback disabled.",
    "Energy above hull <= 0.1 eV for preliminary thermodynamic stability screening.",
    "Band gap is treated as a minimum electronic-insulation screen, not as a rigid target alignment.",
    "Density is advisory and not weighted in the solid-electrolyte preset.",
    "Formula diversity is enforced with maxPerFormula=1 and maxPerFamily=3.",
    "Top candidates must have retrievable structures for downstream Li proxy analysis.",
    "This run still does not compute ionic conductivity, migration barriers, electrochemical windows, or electrode interface reactivity.",
  ],
  rankedCandidates: ranked,
  notePaths: [note.path],
  artifactPaths,
  outputPath: path.join(paths.reportsDir, "live-solid-electrolyte-e2e-v2-report.md"),
  screeningLevel: comparison.data.screeningLevel,
  domainWarnings: [
    "This is a proxy-screen validation run, not a validated solid-electrolyte discovery result.",
    "Li sublattice metrics are geometric descriptors, not measured or simulated ionic conductivity.",
  ],
  methodNotes: [
    "Compared against the earlier E2E weakness where one formula family dominated the top ranks.",
    "Formula diversity was enabled to force a shortlist of distinct hypotheses.",
    "CSV and JSONL ranking artifacts were required for downstream researcher review.",
  ],
  provenance: {
    runRoot,
    generatedAt: new Date().toISOString(),
    dataSource: "Materials Project live API",
    offlineFallbackAllowed: false,
    compareCriteria: comparison.data.criteria,
    pluginPackageVersion: "0.1.0",
  },
});

const formulaCounts = countBy(ranked, (candidate) => candidate.formula);
const familyCounts = countBy(ranked, (candidate) => candidate.family ?? "unknown");
const validation = {
  usedOfflineDataAnywhere:
    searches.some((search) => search.usedOfflineData) ||
    structureRuns.some((run) => run.usedOfflineData),
  solidElectrolytePreset: comparison.data.criteria?.preset === "solid-electrolyte",
  densityUnweighted: Number(comparison.data.criteria?.densityWeight ?? -1) === 0,
  diversityControlsEnabled: Number(comparison.data.criteria?.maxPerFormula ?? 0) === 1,
  rankedMaxFormulaMultiplicity: Math.max(...Object.values(formulaCounts)),
  rankedFamilies: Object.keys(familyCounts).sort(),
  searchFamilies: searches.length,
  totalUniqueCandidates: candidates.length,
  rankedCandidates: ranked.length,
  structuresAnalyzed: structureRuns.length,
  structuresWithLiProxyMetrics: structureRuns.filter((run) => typeof run.summaryMetrics?.liCount === "number").length,
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
  topic: "solid-state lithium battery electrolyte screening v2",
  liveMaterialsProject: true,
  searches,
  totalUniqueCandidates: candidates.length,
  comparison: comparison.data,
  rankedCandidates: ranked,
  formulaCounts,
  familyCounts,
  structuresAnalyzed: structureRuns,
  structureFailures,
  notePath: note.path,
  reportPath: report.data.outputPath,
  artifactPaths,
  validation,
};

const summaryPath = path.join(paths.reportsDir, "live-solid-electrolyte-e2e-v2-summary.json");
await fs.writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");

const processReportPath = path.join(paths.reportsDir, "live-openclaw-solid-electrolyte-e2e-v2-process.md");
await fs.writeFile(
  processReportPath,
  [
    "# Live OpenClaw Materials Lab Solid Electrolyte E2E V2 Process",
    "",
    `Generated: ${summary.generatedAt}`,
    "",
    "## Question",
    "",
    "Can the patched solid-electrolyte preset produce a more diverse, better-labeled live Materials Project proxy shortlist?",
    "",
    "## Patch Validation Targets",
    "",
    `- Solid-electrolyte preset applied: ${validation.solidElectrolytePreset}`,
    `- Density unweighted/advisory: ${validation.densityUnweighted}`,
    `- Formula diversity max multiplicity: ${validation.rankedMaxFormulaMultiplicity}`,
    `- Ranking artifacts include table exports: ${(comparison.data.tablePaths ?? []).length >= 2}`,
    `- Structures with Li proxy metrics: ${validation.structuresWithLiProxyMetrics}`,
    "",
    "## Validation",
    "",
    `- Offline fallback used anywhere: ${validation.usedOfflineDataAnywhere}`,
    `- Search families: ${validation.searchFamilies}`,
    `- Unique live candidates: ${validation.totalUniqueCandidates}`,
    `- Ranked candidates after diversity controls: ${validation.rankedCandidates}`,
    `- Ranked families: ${validation.rankedFamilies.join(", ")}`,
    `- Structures analyzed: ${validation.structuresAnalyzed}`,
    `- Required artifacts exist: ${validation.requiredArtifactsExist.ok}`,
    "",
    "## Outputs",
    "",
    `- Summary JSON: ${summaryPath}`,
    `- Final report: ${report.data.outputPath}`,
    `- Process note: ${note.path}`,
    `- Ranking/table artifacts: ${(comparison.artifacts ?? []).join(", ")}`,
    "",
    "## Top Candidates",
    "",
    ...ranked.slice(0, 10).map(
      (candidate) =>
        `- ${candidate.rank}. ${candidate.materialId} (${candidate.formula}, ${candidate.family}) score=${candidate.score}, rawRank=${candidate.rawRank}, bandGap=${candidate.bandGapEv}, eHull=${candidate.energyAboveHullEv}`,
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
      tablePaths: comparison.data.tablePaths,
      topCandidates: ranked.slice(0, 8).map((candidate) => ({
        rank: candidate.rank,
        rawRank: candidate.rawRank,
        materialId: candidate.materialId,
        formula: candidate.formula,
        family: candidate.family,
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

function countBy(items, keyFn) {
  const counts = {};
  for (const item of items) {
    const key = String(keyFn(item));
    counts[key] = (counts[key] ?? 0) + 1;
  }
  return counts;
}

function slugForPath(value) {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
