import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { resolveWorkspacePaths } from "../../dist/src/core/paths.js";
import { PythonBridgeService } from "../../dist/src/services/python-bridge.js";
import { ArtifactService } from "../../dist/src/services/artifact-service.js";
import { NoteService } from "../../dist/src/services/note-service.js";

const repoRoot = path.resolve(new URL("../..", import.meta.url).pathname);
const runRoot = path.join(repoRoot, "materials-lab-runs", "high-k-dielectric-live-e2e-20260503");
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

const formulaQueries = [
  "HfO2",
  "ZrO2",
  "Al2O3",
  "SiO2",
  "Y2O3",
  "La2O3",
  "Ta2O5",
  "TiO2",
  "SrTiO3",
  "BaTiO3",
];

const searches = [];
const candidateById = new Map();

for (const formula of formulaQueries) {
  const payload = {
    formula,
    maxEnergyAboveHullEv: 0.08,
    minBandGapEv: 2.0,
    maxBandGapEv: 9.5,
    limit: 12,
    allowOffline: false,
  };
  const result = await bridge.searchMaterials(payload);
  const candidates = result.data.candidates ?? [];
  searches.push({
    label: `${formula} high-k/wide-gap oxide family`,
    payload,
    summary: result.summary,
    usedOfflineData: result.data.usedOfflineData,
    candidateCount: candidates.length,
    candidateIds: candidates.map((candidate) => candidate.materialId),
  });
  if (result.data.usedOfflineData) {
    throw new Error(`Live Materials Project validation failed: ${formula} used offline data.`);
  }
  for (const candidate of candidates) {
    if (candidate?.materialId && !candidateById.has(candidate.materialId)) {
      candidateById.set(candidate.materialId, candidate);
    }
  }
}

const candidates = [...candidateById.values()];
if (candidates.length < 5) {
  throw new Error(`Expected at least 5 live candidates, got ${candidates.length}.`);
}

const compareDir = path.join(paths.plotsDir, "high-k-dielectric-ranking");
const comparison = await bridge.compareCandidates({
  candidates,
  criteria: {
    preset: "generic",
    screeningLevel: "proxy-screen",
    stabilityWeight: 0.45,
    bandGapWeight: 0.40,
    densityWeight: 0.15,
    bandGapScoringMode: "target",
    bandGapTargetEv: 5.5,
    densityScoringMode: "target",
    densityTargetGcm3: 6.0,
    diversifyBy: "formula",
    maxPerFormula: 1,
  },
  topK: Math.min(10, candidates.length),
  artifactDir: compareDir,
});

const ranked = comparison.data.ranked ?? [];
if (ranked.length < 3) {
  throw new Error(`Expected at least 3 ranked candidates, got ${ranked.length}.`);
}

const structureRuns = [];
const structureFailures = [];
const artifactPaths = [...(comparison.artifacts ?? [])];

for (const candidate of ranked.slice(0, Math.min(5, ranked.length))) {
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
  title: "Live Materials Project high-k dielectric oxide screening process",
  noteType: "process",
  tags: ["materials-project", "dielectric", "high-k", "oxide", "openclaw-e2e"],
  candidateIds: ranked.map((candidate) => candidate.materialId),
  artifactPaths,
  body: [
    "Question: Which stable wide-bandgap oxide candidates are worth shortlisting as high-k dielectric proxy candidates?",
    "",
    "Process:",
    "1. Queried live Materials Project formula families for common high-k/wide-bandgap oxides.",
    "2. Disabled offline fallback in every query and structure fetch.",
    "3. Ranked candidates with a generic proxy score emphasizing stability, wide band gap near 5.5 eV, and density near 6.0 g/cm3.",
    "4. Enforced formula diversity to avoid repeated polymorph domination.",
    "5. Exported ranking PNG plus CSV/JSONL table artifacts.",
    "6. Fetched JSON/CIF structures for top ranked candidates and generated unit-aware metric plots.",
    "7. Exported an enhanced markdown report and machine-readable validation summary.",
  ].join("\n"),
});

const report = await bridge.exportReport({
  title: "Live Materials Project High-k Dielectric Oxide Proxy Screening",
  goal:
    "Use OpenClaw Materials Lab with live Materials Project data to validate a non-battery proxy workflow for stable wide-bandgap oxide gate-dielectric candidates.",
  evaluationCriteria: [
    "Live Materials Project source only; offline fallback disabled.",
    "Energy above hull <= 0.08 eV for preliminary thermodynamic stability screening.",
    "Band gap ranked toward 5.5 eV as a proxy for low leakage and insulating behavior.",
    "Density ranked toward 6.0 g/cm3 as a weak proxy for heavy-cation oxide dielectric families.",
    "Formula diversity is enforced with maxPerFormula=1.",
    "This run does not compute dielectric constant, band offsets to Si, leakage current, phonon stability, amorphizability, or interface reactions.",
  ],
  rankedCandidates: ranked,
  notePaths: [note.path],
  artifactPaths,
  outputPath: path.join(paths.reportsDir, "live-high-k-dielectric-e2e-report.md"),
  screeningLevel: comparison.data.screeningLevel,
  domainWarnings: [
    "This is a proxy-screen validation run, not a validated gate-dielectric discovery result.",
    "The current plugin does not fetch or compute dielectric tensors, band offsets, leakage barriers, or interface stability.",
  ],
  methodNotes: [
    "This E2E intentionally uses a non-Li, non-battery topic to test whether the plugin generalizes beyond solid electrolytes.",
    "Ranking is based on generic Materials Project summary fields and should be treated as a triage view only.",
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

const validation = {
  usedOfflineDataAnywhere:
    searches.some((search) => search.usedOfflineData) ||
    structureRuns.some((run) => run.usedOfflineData),
  searchFamilies: searches.length,
  totalUniqueCandidates: candidates.length,
  rankedCandidates: ranked.length,
  rankedFormulaMultiplicityMax: Math.max(...Object.values(countBy(ranked, (candidate) => candidate.formula))),
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
  topic: "high-k dielectric oxide proxy screening",
  liveMaterialsProject: true,
  searches,
  totalUniqueCandidates: candidates.length,
  comparison: comparison.data,
  rankedCandidates: ranked,
  structuresAnalyzed: structureRuns,
  structureFailures,
  notePath: note.path,
  reportPath: report.data.outputPath,
  artifactPaths,
  validation,
};

const summaryPath = path.join(paths.reportsDir, "live-high-k-dielectric-e2e-summary.json");
await fs.writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");

const processReportPath = path.join(paths.reportsDir, "live-openclaw-high-k-dielectric-e2e-process.md");
await fs.writeFile(
  processReportPath,
  [
    "# Live OpenClaw Materials Lab High-k Dielectric E2E Process",
    "",
    `Generated: ${summary.generatedAt}`,
    "",
    "## Question",
    "",
    "Can Materials Lab produce a useful live proxy shortlist for stable wide-bandgap oxide gate dielectrics?",
    "",
    "## Validation",
    "",
    `- Offline fallback used anywhere: ${validation.usedOfflineDataAnywhere}`,
    `- Search formula families: ${validation.searchFamilies}`,
    `- Unique live candidates: ${validation.totalUniqueCandidates}`,
    `- Ranked candidates: ${validation.rankedCandidates}`,
    `- Formula diversity max multiplicity: ${validation.rankedFormulaMultiplicityMax}`,
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
      topCandidates: ranked.slice(0, 8).map((candidate) => ({
        rank: candidate.rank,
        rawRank: candidate.rawRank,
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
