import { Type, type Static } from "@sinclair/typebox";
import type { OpenClawToolDefinition } from "openclaw/plugin-sdk/plugin-entry";

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
  },
  { additionalProperties: false },
);

const CompareSchema = Type.Object(
  {
    candidates: Type.Array(CandidateSchema, { minItems: 2, maxItems: 50 }),
    criteria: Type.Optional(
      Type.Object(
        {
          stabilityWeight: Type.Optional(Type.Number({ minimum: 0, maximum: 1 })),
          bandGapWeight: Type.Optional(Type.Number({ minimum: 0, maximum: 1 })),
          densityWeight: Type.Optional(Type.Number({ minimum: 0, maximum: 1 })),
          bandGapTargetEv: Type.Optional(Type.Number({ minimum: 0 })),
          densityTargetGcm3: Type.Optional(Type.Number({ minimum: 0 })),
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
): OpenClawToolDefinition<typeof CompareSchema> {
  return {
    name: "materials_compare_candidates",
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
