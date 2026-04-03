import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool } from "openclaw/plugin-sdk/plugin-entry";

import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { toToolResponse } from "../types/tool-results.js";
import { payloadFromBridge } from "./shared.js";

const SearchSchema = Type.Object(
  {
    textQuery: Type.Optional(Type.String({ maxLength: 200 })),
    formula: Type.Optional(Type.String({ maxLength: 80 })),
    elementsAll: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 3 }), { maxItems: 12 })),
    elementsAny: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 3 }), { maxItems: 12 })),
    maxEnergyAboveHullEv: Type.Optional(Type.Number({ minimum: 0 })),
    minBandGapEv: Type.Optional(Type.Number({ minimum: 0 })),
    maxBandGapEv: Type.Optional(Type.Number({ minimum: 0 })),
    limit: Type.Optional(Type.Number({ minimum: 1, maximum: 100 })),
    allowOffline: Type.Optional(Type.Boolean({ default: true })),
  },
  { additionalProperties: false },
);

export type MaterialsSearchParams = Static<typeof SearchSchema>;

export function createMaterialsSearchTool(context: MaterialsPluginContext): AnyAgentTool {
  return {
    name: "materials_search_mp",
    label: "Search Materials",
    description: "Search Materials Project or the bundled offline dataset for candidate materials.",
    parameters: SearchSchema,
    async execute(_callId, rawParams) {
      const params = rawParams as MaterialsSearchParams;
      const artifactService = context.getArtifactService();
      await artifactService.ensureReady();
      const bridgeResult = await context.getBridge().searchMaterials({
        ...params,
        limit: params.limit ?? 10,
        allowOffline: params.allowOffline ?? true,
      });

      return toToolResponse(payloadFromBridge(artifactService, bridgeResult));
    },
  };
}
