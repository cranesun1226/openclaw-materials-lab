import path from "node:path";

import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool } from "openclaw/plugin-sdk/plugin-entry";

import { ensureWithinRoot } from "../core/paths.js";
import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { toToolResponse } from "../types/tool-results.js";
import { payloadFromBridge } from "./shared.js";

const ExecuteResearchPlanSchema = Type.Object(
  {
    planPath: Type.Optional(Type.String({ minLength: 1 })),
    plan: Type.Optional(Type.Record(Type.String(), Type.Any())),
    backend: Type.Optional(Type.Literal("local-surrogate")),
    maxSteps: Type.Optional(Type.Number({ minimum: 1, maximum: 500 })),
    allowBlockedSurrogate: Type.Optional(Type.Boolean()),
  },
  { additionalProperties: false },
);

export type MaterialsExecuteResearchPlanParams = Static<typeof ExecuteResearchPlanSchema>;

export function createMaterialsExecuteResearchPlanTool(
  context: MaterialsPluginContext,
): AnyAgentTool {
  return {
    name: "materials_execute_research_plan",
    label: "Execute Research Plan",
    description: "Execute an approval-gated research plan through a configured backend adapter.",
    parameters: ExecuteResearchPlanSchema,
    async execute(_callId, rawParams) {
      const params = rawParams as MaterialsExecuteResearchPlanParams;
      const artifactService = context.getArtifactService();
      const workspacePaths = artifactService.getPaths();
      await artifactService.ensureReady();

      const planPath = params.planPath
        ? ensureWithinRoot(workspacePaths.workspaceRoot, params.planPath, "planPath")
        : undefined;
      const artifactDir = ensureWithinRoot(
        workspacePaths.reportsDir,
        path.join(workspacePaths.reportsDir, "research-loop-executions"),
        "research execution artifact dir",
      );
      const bridgeResult = await context.getBridge().executeResearchPlan({
        artifactDir,
        backend: params.backend ?? "local-surrogate",
        ...(planPath ? { planPath } : {}),
        ...(params.plan ? { plan: params.plan } : {}),
        ...(typeof params.maxSteps === "number" ? { maxSteps: params.maxSteps } : {}),
        ...(typeof params.allowBlockedSurrogate === "boolean" ? { allowBlockedSurrogate: params.allowBlockedSurrogate } : {}),
      });

      return toToolResponse(payloadFromBridge(artifactService, bridgeResult));
    },
  };
}
