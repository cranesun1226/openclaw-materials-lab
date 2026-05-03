import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool } from "openclaw/plugin-sdk/plugin-entry";

import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { toToolResponse } from "../types/tool-results.js";
import { payloadFromBridge } from "./shared.js";

const CandidateSchema = Type.Object(
  {
    materialId: Type.String({ minLength: 1, maxLength: 80 }),
    formula: Type.String({ minLength: 1, maxLength: 80 }),
    energyAboveHullEv: Type.Optional(Type.Number({ minimum: 0 })),
    bandGapEv: Type.Optional(Type.Number({ minimum: 0 })),
    densityGcm3: Type.Optional(Type.Number({ minimum: 0 })),
    volume: Type.Optional(Type.Number({ minimum: 0 })),
    sites: Type.Optional(Type.Number({ minimum: 1 })),
    spacegroup: Type.Optional(Type.String({ minLength: 1, maxLength: 80 })),
    elements: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 3 }), { maxItems: 20 })),
    source: Type.Union([Type.Literal("materials-project"), Type.Literal("mock")]),
    notes: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 200 }), { maxItems: 20 })),
    materialsProjectUrl: Type.Optional(Type.String({ minLength: 1, maxLength: 300 })),
    family: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
    duplicateGroup: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
    duplicateCount: Type.Optional(Type.Number({ minimum: 1 })),
    warnings: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 300 }), { maxItems: 50 })),
    screeningLevel: Type.Optional(Type.String({ minLength: 1, maxLength: 80 })),
    riskProfile: Type.Optional(Type.Record(Type.String(), Type.Any())),
    compositionDescriptors: Type.Optional(Type.Record(Type.String(), Type.Any())),
  },
  { additionalProperties: false },
);

const CompareSchema = Type.Object(
  {
    candidates: Type.Array(CandidateSchema, { minItems: 2, maxItems: 50 }),
    criteria: Type.Optional(
      Type.Object(
        {
          preset: Type.Optional(Type.Union([Type.Literal("generic"), Type.Literal("solid-electrolyte")])),
          screeningLevel: Type.Optional(
            Type.Union([
              Type.Literal("technical-smoke"),
              Type.Literal("proxy-screen"),
              Type.Literal("research-shortlist"),
              Type.Literal("validated-candidate"),
            ]),
          ),
          stabilityWeight: Type.Optional(Type.Number({ minimum: 0, maximum: 1 })),
          bandGapWeight: Type.Optional(Type.Number({ minimum: 0, maximum: 1 })),
          densityWeight: Type.Optional(Type.Number({ minimum: 0, maximum: 1 })),
          bandGapScoringMode: Type.Optional(Type.Union([Type.Literal("target"), Type.Literal("minimum")])),
          minimumBandGapEv: Type.Optional(Type.Number({ minimum: 0 })),
          bandGapTargetEv: Type.Optional(Type.Number({ minimum: 0 })),
          densityScoringMode: Type.Optional(Type.Union([Type.Literal("target"), Type.Literal("advisory"), Type.Literal("none")])),
          densityTargetGcm3: Type.Optional(Type.Number({ minimum: 0 })),
          secondaryWeight: Type.Optional(Type.Number({ minimum: 0, maximum: 0.5 })),
          riskPenaltyWeight: Type.Optional(Type.Number({ minimum: 0, maximum: 1 })),
          preferredBandGapEv: Type.Optional(Type.Number({ minimum: 0 })),
          preferredLiFractionMin: Type.Optional(Type.Number({ minimum: 0, maximum: 1 })),
          preferredLiFractionMax: Type.Optional(Type.Number({ minimum: 0, maximum: 1 })),
          excludeToxicElements: Type.Optional(Type.Boolean()),
          excludeRiskyChemistry: Type.Optional(Type.Boolean()),
          filterMolecularSalts: Type.Optional(Type.Boolean()),
          requiresLithium: Type.Optional(Type.Boolean()),
          excludedElements: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 3 }), { maxItems: 40 })),
          flaggedElements: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 3 }), { maxItems: 40 })),
          maxHydrogenAtomicFraction: Type.Optional(Type.Number({ minimum: 0, maximum: 1 })),
          diversifyBy: Type.Optional(
            Type.Union([
              Type.Literal("none"),
              Type.Literal("formula"),
              Type.Literal("family"),
              Type.Literal("formula-and-family"),
            ]),
          ),
          maxPerFormula: Type.Optional(Type.Number({ minimum: 0, maximum: 50 })),
          maxPerFamily: Type.Optional(Type.Number({ minimum: 0, maximum: 50 })),
        },
        { additionalProperties: false },
      ),
    ),
    topK: Type.Optional(Type.Number({ minimum: 1, maximum: 50 })),
  },
  { additionalProperties: false },
);

export type MaterialsCompareCandidatesParams = Static<typeof CompareSchema>;

export function createMaterialsCompareCandidatesTool(
  context: MaterialsPluginContext,
): AnyAgentTool {
  return {
    name: "materials_compare_candidates",
    label: "Compare Candidates",
    description: "Compare candidate materials and rank them by configurable criteria.",
    parameters: CompareSchema,
    async execute(_callId, rawParams) {
      const params = rawParams as MaterialsCompareCandidatesParams;
      const artifactService = context.getArtifactService();
      await artifactService.ensureReady();

      const bridgeResult = await context.getBridge().compareCandidates({
        candidates: params.candidates,
        artifactDir: artifactService.createPlotDir(),
        ...(params.criteria ? { criteria: params.criteria } : {}),
        ...(typeof params.topK === "number" ? { topK: params.topK } : {}),
      });

      return toToolResponse(payloadFromBridge(artifactService, bridgeResult));
    },
  };
}
