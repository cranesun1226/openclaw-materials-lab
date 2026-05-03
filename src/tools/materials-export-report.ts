import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool } from "openclaw/plugin-sdk/plugin-entry";

import { ensureWithinRoot } from "../core/paths.js";
import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { toToolResponse } from "../types/tool-results.js";
import { payloadFromBridge } from "./shared.js";

const RankedCandidateSchema = Type.Object(
  {
    materialId: Type.String({ minLength: 1, maxLength: 80 }),
    formula: Type.String({ minLength: 1, maxLength: 80 }),
    source: Type.Union([Type.Literal("materials-project"), Type.Literal("dev-fixture")]),
    score: Type.Number(),
    primaryScore: Type.Optional(Type.Number()),
    secondaryScore: Type.Optional(Type.Number()),
    domainEvidenceScore: Type.Optional(Type.Number()),
    riskPenalty: Type.Optional(Type.Number()),
    rank: Type.Number({ minimum: 1 }),
    reasons: Type.Array(Type.String({ minLength: 1 }), { maxItems: 20 }),
    energyAboveHullEv: Type.Optional(Type.Number({ minimum: 0 })),
    bandGapEv: Type.Optional(Type.Number({ minimum: 0 })),
    densityGcm3: Type.Optional(Type.Number({ minimum: 0 })),
    volume: Type.Optional(Type.Number({ minimum: 0 })),
    sites: Type.Optional(Type.Number({ minimum: 1 })),
    spacegroup: Type.Optional(Type.String({ minLength: 1, maxLength: 80 })),
    elements: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 3 }), { maxItems: 20 })),
    notes: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 200 }), { maxItems: 20 })),
    materialsProjectUrl: Type.Optional(Type.String({ minLength: 1, maxLength: 300 })),
    family: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
    duplicateGroup: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
    duplicateCount: Type.Optional(Type.Number({ minimum: 1 })),
    rawRank: Type.Optional(Type.Number({ minimum: 1 })),
    warnings: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 300 }), { maxItems: 50 })),
    screeningLevel: Type.Optional(Type.String({ minLength: 1, maxLength: 80 })),
    scoreComponents: Type.Optional(Type.Any()),
    riskProfile: Type.Optional(Type.Record(Type.String(), Type.Any())),
    compositionDescriptors: Type.Optional(Type.Record(Type.String(), Type.Any())),
    domainEvidence: Type.Optional(Type.Record(Type.String(), Type.Any())),
    dielectricTotal: Type.Optional(Type.Number({ minimum: 0 })),
    dielectricElectronic: Type.Optional(Type.Number({ minimum: 0 })),
    bandOffsetElectronEv: Type.Optional(Type.Number()),
    bandOffsetHoleEv: Type.Optional(Type.Number()),
    interfaceReactionEnergyEv: Type.Optional(Type.Number()),
    ionicConductivityScm: Type.Optional(Type.Number({ minimum: 0 })),
    migrationBarrierEv: Type.Optional(Type.Number({ minimum: 0 })),
    electrochemicalWindowV: Type.Optional(Type.Number({ minimum: 0 })),
    absorptionCoefficientCm1: Type.Optional(Type.Number({ minimum: 0 })),
    directBandGapEv: Type.Optional(Type.Number({ minimum: 0 })),
    effectiveMassElectron: Type.Optional(Type.Number({ minimum: 0 })),
    effectiveMassHole: Type.Optional(Type.Number({ minimum: 0 })),
    seebeckUvK: Type.Optional(Type.Number()),
    powerFactorUwCmK2: Type.Optional(Type.Number({ minimum: 0 })),
    latticeThermalConductivityWmK: Type.Optional(Type.Number({ minimum: 0 })),
    carrierConcentrationCm3: Type.Optional(Type.Number({ minimum: 0 })),
    phononStability: Type.Optional(Type.Number({ minimum: 0, maximum: 1 })),
    cbmEv: Type.Optional(Type.Number()),
    vbmEv: Type.Optional(Type.Number()),
    defectToleranceScore: Type.Optional(Type.Number({ minimum: 0, maximum: 1 })),
    structureQuality: Type.Optional(Type.Number({ minimum: 0, maximum: 1 })),
    propertyProvenance: Type.Optional(Type.Record(Type.String(), Type.Any())),
    calculationStatus: Type.Optional(Type.Record(Type.String(), Type.Any())),
  },
  { additionalProperties: false },
);

const ExportReportSchema = Type.Object(
  {
    title: Type.String({ minLength: 1, maxLength: 160 }),
    goal: Type.String({ minLength: 1 }),
    evaluationCriteria: Type.Array(Type.String({ minLength: 1, maxLength: 300 }), { minItems: 1, maxItems: 20 }),
    rankedCandidates: Type.Array(RankedCandidateSchema, { minItems: 1, maxItems: 50 }),
    notePaths: Type.Optional(Type.Array(Type.String({ minLength: 1 }), { maxItems: 100 })),
    artifactPaths: Type.Optional(Type.Array(Type.String({ minLength: 1 }), { maxItems: 100 })),
    screeningLevel: Type.Optional(Type.String({ minLength: 1, maxLength: 80 })),
    domainWarnings: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 300 }), { maxItems: 50 })),
    methodNotes: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 300 }), { maxItems: 50 })),
    provenance: Type.Optional(Type.Record(Type.String(), Type.Any())),
    fileName: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
  },
  { additionalProperties: false },
);

export type MaterialsExportReportParams = Static<typeof ExportReportSchema>;

export function createMaterialsExportReportTool(context: MaterialsPluginContext): AnyAgentTool {
  return {
    name: "materials_export_report",
    label: "Export Report",
    description: "Export a markdown research report that references notes and generated artifacts.",
    parameters: ExportReportSchema,
    async execute(_callId, rawParams) {
      const params = rawParams as MaterialsExportReportParams;
      const artifactService = context.getArtifactService();
      const workspacePaths = artifactService.getPaths();
      await artifactService.ensureReady();

      const outputPath = artifactService.createReportPath(params.title, params.fileName);
      const notePaths = (params.notePaths ?? []).map((notePath) =>
        ensureWithinRoot(workspacePaths.workspaceRoot, notePath, "notePath"),
      );
      const artifactPaths = (params.artifactPaths ?? []).map((artifactPath) =>
        ensureWithinRoot(workspacePaths.workspaceRoot, artifactPath, "artifactPath"),
      );

      const bridgeResult = await context.getBridge().exportReport({
        title: params.title,
        goal: params.goal,
        evaluationCriteria: params.evaluationCriteria,
        rankedCandidates: params.rankedCandidates,
        notePaths,
        artifactPaths,
        ...(params.screeningLevel ? { screeningLevel: params.screeningLevel } : {}),
        ...(params.domainWarnings ? { domainWarnings: params.domainWarnings } : {}),
        ...(params.methodNotes ? { methodNotes: params.methodNotes } : {}),
        ...(params.provenance ? { provenance: params.provenance } : {}),
        outputPath,
      });

      return toToolResponse(payloadFromBridge(artifactService, bridgeResult));
    },
  };
}
