import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool } from "openclaw/plugin-sdk/plugin-entry";

import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { toToolResponse } from "../types/tool-results.js";
import { payloadFromBridge } from "./shared.js";

const BatchScreenSchema = Type.Object(
  {
    candidateIds: Type.Array(Type.String({ minLength: 1, maxLength: 80 }), { minItems: 1, maxItems: 500 }),
    limit: Type.Optional(Type.Number({ minimum: 1, maximum: 500 })),
    allowOffline: Type.Optional(Type.Boolean({ default: true })),
  },
  { additionalProperties: false },
);

export type MaterialsBatchScreenParams = Static<typeof BatchScreenSchema>;

export function createMaterialsBatchScreenTool(
  context: MaterialsPluginContext,
): AnyAgentTool {
  return {
    name: "materials_batch_screen",
    label: "Batch Screen",
    description: "Run an approval-gated batch screening workflow across multiple candidate ids.",
    parameters: BatchScreenSchema,
    async execute(_callId, rawParams) {
      const params = rawParams as MaterialsBatchScreenParams;
      const artifactService = context.getArtifactService();
      await artifactService.ensureReady();
      const bridgeResult = await context.getBridge().batchScreen({
        candidateIds: params.candidateIds,
        limit: params.limit ?? context.resolveConfig().defaultBatchLimit,
        artifactDir: artifactService.createPlotDir(),
        allowOffline: params.allowOffline ?? true,
      });

      return toToolResponse(payloadFromBridge(artifactService, bridgeResult));
    },
  };
}
