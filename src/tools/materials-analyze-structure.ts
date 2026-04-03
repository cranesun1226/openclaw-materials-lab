import { Type, type Static } from "@sinclair/typebox";
import type { OpenClawToolDefinition } from "openclaw/plugin-sdk/plugin-entry";

import { ensureWithinRoot } from "../core/paths.js";
import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { toToolResponse } from "../types/tool-results.js";
import { payloadFromBridge } from "./shared.js";

const AnalyzeStructureSchema = Type.Object(
  {
    materialId: Type.Optional(Type.String({ minLength: 1, maxLength: 80 })),
    structurePath: Type.Optional(Type.String({ minLength: 1 })),
    allowOffline: Type.Optional(Type.Boolean({ default: true })),
  },
  { additionalProperties: false },
);

export type MaterialsAnalyzeStructureParams = Static<typeof AnalyzeStructureSchema>;

export function createMaterialsAnalyzeStructureTool(
  context: MaterialsPluginContext,
): OpenClawToolDefinition<typeof AnalyzeStructureSchema> {
  return {
    name: "materials_analyze_structure",
    description: "Analyze a material structure with pymatgen-aware local tooling and return derived metrics.",
    parameters: AnalyzeStructureSchema,
    async execute(_callId, rawParams) {
      const params = rawParams as MaterialsAnalyzeStructureParams;
      const artifactService = context.getArtifactService();
      const workspacePaths = artifactService.getPaths();
      await artifactService.ensureReady();

      const structurePath = params.structurePath
        ? ensureWithinRoot(workspacePaths.workspaceRoot, params.structurePath, "structurePath")
        : undefined;

      const artifactDir = params.materialId
        ? artifactService.createStructureArtifactDir(params.materialId)
        : workspacePaths.plotsDir;

      const bridgeResult = await context.getBridge().analyzeStructure({
        ...(params.materialId ? { materialId: params.materialId } : {}),
        ...(structurePath ? { structurePath } : {}),
        artifactDir,
        allowOffline: params.allowOffline ?? true,
      });

      return toToolResponse(payloadFromBridge(artifactService, bridgeResult));
    },
  };
}
