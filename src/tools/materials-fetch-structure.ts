import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool } from "openclaw/plugin-sdk/plugin-entry";

import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { toToolResponse } from "../types/tool-results.js";
import { payloadFromBridge } from "./shared.js";

const FetchStructureSchema = Type.Object(
  {
    materialId: Type.String({ minLength: 1, maxLength: 80 }),
    format: Type.Optional(Type.Union([Type.Literal("json"), Type.Literal("cif"), Type.Literal("both")])),
    allowOffline: Type.Optional(Type.Boolean({ default: true })),
  },
  { additionalProperties: false },
);

export type MaterialsFetchStructureParams = Static<typeof FetchStructureSchema>;

export function createMaterialsFetchStructureTool(
  context: MaterialsPluginContext,
): AnyAgentTool {
  return {
    name: "materials_fetch_structure",
    label: "Fetch Structure",
    description: "Fetch a material structure and save local structure artifacts under workspaceRoot.",
    parameters: FetchStructureSchema,
    async execute(_callId, rawParams) {
      const params = rawParams as MaterialsFetchStructureParams;
      const artifactService = context.getArtifactService();
      await artifactService.ensureReady();
      const artifactDir = artifactService.createStructureArtifactDir(params.materialId);
      const bridgeResult = await context.getBridge().fetchStructure({
        materialId: params.materialId,
        format: params.format ?? "both",
        artifactDir,
        allowOffline: params.allowOffline ?? true,
      });

      return toToolResponse(payloadFromBridge(artifactService, bridgeResult));
    },
  };
}
