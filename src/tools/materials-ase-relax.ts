import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool } from "openclaw/plugin-sdk/plugin-entry";

import { ConfigurationError } from "../core/errors.js";
import { ensureWithinRoot } from "../core/paths.js";
import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { toToolResponse } from "../types/tool-results.js";
import { payloadFromBridge } from "./shared.js";

const AseRelaxSchema = Type.Object(
  {
    materialId: Type.Optional(Type.String({ minLength: 1, maxLength: 80 })),
    structurePath: Type.Optional(Type.String({ minLength: 1 })),
    steps: Type.Optional(Type.Number({ minimum: 1, maximum: 5000 })),
    fmaxEvA: Type.Optional(Type.Number({ minimum: 0.0001, maximum: 1 })),
    calculator: Type.Optional(
      Type.String({
        minLength: 1,
        maxLength: 40,
        description: "ASE calculator to use. Supported values are EMT and SevenNet.",
      }),
    ),
    sevenNetModel: Type.Optional(
      Type.String({
        minLength: 1,
        maxLength: 300,
        description: "SevenNet pretrained model keyword or local checkpoint path. Defaults to 7net-omni.",
      }),
    ),
    sevenNetModal: Type.Optional(
      Type.String({
        minLength: 1,
        maxLength: 80,
        description: "SevenNet modal label for multi-modal pretrained models. Defaults to mpa.",
      }),
    ),
    device: Type.Optional(
      Type.String({
        minLength: 1,
        maxLength: 40,
        description: "SevenNet execution device, such as auto, cpu, cuda, or cuda:0. Defaults to auto.",
      }),
    ),
    allowOffline: Type.Optional(Type.Boolean({ default: false })),
  },
  { additionalProperties: false },
);

export type MaterialsAseRelaxParams = Static<typeof AseRelaxSchema>;

export function createMaterialsAseRelaxTool(context: MaterialsPluginContext): AnyAgentTool {
  return {
    name: "materials_ase_relax",
    label: "ASE Relax",
    description: "Run an approval-gated local ASE relaxation workflow.",
    parameters: AseRelaxSchema,
    async execute(_callId, rawParams) {
      const config = context.resolveConfig();
      if (!config.enableAseTools) {
        throw new ConfigurationError("ASE tools are disabled for this plugin instance.", {
          hint: "Set enableAseTools to true in plugins.entries.materials-lab.config before using materials_ase_relax.",
        });
      }

      const params = rawParams as MaterialsAseRelaxParams;
      const artifactService = context.getArtifactService();
      const workspacePaths = artifactService.getPaths();
      await artifactService.ensureReady();

      const structurePath = params.structurePath
        ? ensureWithinRoot(workspacePaths.workspaceRoot, params.structurePath, "structurePath")
        : undefined;

      const artifactDir = params.materialId
        ? artifactService.createStructureArtifactDir(params.materialId)
        : artifactService.createPlotDir();

      const bridgeResult = await context.getBridge().aseRelax({
        ...(params.materialId ? { materialId: params.materialId } : {}),
        ...(structurePath ? { structurePath } : {}),
        artifactDir,
        ...(typeof params.steps === "number" ? { steps: params.steps } : {}),
        ...(typeof params.fmaxEvA === "number" ? { fmaxEvA: params.fmaxEvA } : {}),
        ...(params.calculator ? { calculator: params.calculator } : {}),
        ...(params.sevenNetModel ? { sevenNetModel: params.sevenNetModel } : {}),
        ...(params.sevenNetModal ? { sevenNetModal: params.sevenNetModal } : {}),
        ...(params.device ? { device: params.device } : {}),
        allowOffline: params.allowOffline ?? false,
      });

      return toToolResponse(payloadFromBridge(artifactService, bridgeResult));
    },
  };
}
