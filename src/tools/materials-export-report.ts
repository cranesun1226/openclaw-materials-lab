import { Type, type Static } from "@sinclair/typebox";
import type { OpenClawToolDefinition } from "openclaw/plugin-sdk/plugin-entry";

import { ensureWithinRoot } from "../core/paths.js";
import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { toToolResponse } from "../types/tool-results.js";
import { payloadFromBridge } from "./shared.js";

const RankedCandidateSchema = Type.Object(
  {
    materialId: Type.String({ minLength: 1, maxLength: 80 }),
    formula: Type.String({ minLength: 1, maxLength: 80 }),
    source: Type.Union([Type.Literal("materials-project"), Type.Literal("mock")]),
    score: Type.Number(),
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
    fileName: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
  },
  { additionalProperties: false },
);

export type MaterialsExportReportParams = Static<typeof ExportReportSchema>;

export function createMaterialsExportReportTool(
  context: MaterialsPluginContext,
): OpenClawToolDefinition<typeof ExportReportSchema> {
  return {
    name: "materials_export_report",
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
        outputPath,
      });

      return toToolResponse(payloadFromBridge(artifactService, bridgeResult));
    },
  };
}
