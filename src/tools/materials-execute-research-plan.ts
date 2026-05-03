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
    backend: Type.Optional(
      Type.Union([
        Type.Literal("dev-smoke"),
        Type.Literal("quantum-espresso"),
        Type.Literal("vasp"),
        Type.Literal("atomate2"),
        Type.Literal("aiida"),
      ]),
    ),
    executionMode: Type.Optional(Type.Union([Type.Literal("prepare"), Type.Literal("submit"), Type.Literal("monitor")])),
    executionManifestPath: Type.Optional(Type.String({ minLength: 1 })),
    maxSteps: Type.Optional(Type.Number({ minimum: 1, maximum: 500 })),
    allowBlockedDevSmoke: Type.Optional(Type.Boolean()),
    allowExecution: Type.Optional(Type.Boolean()),
    backendConfig: Type.Optional(Type.Record(Type.String(), Type.Any())),
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
      const executionManifestPath = params.executionManifestPath
        ? ensureWithinRoot(workspacePaths.workspaceRoot, params.executionManifestPath, "executionManifestPath")
        : undefined;
      const artifactDir = ensureWithinRoot(
        workspacePaths.reportsDir,
        path.join(workspacePaths.reportsDir, "research-loop-executions"),
        "research execution artifact dir",
      );
      const bridgeResult = await context.getBridge().executeResearchPlan({
        artifactDir,
        backend: params.backend ?? "dev-smoke",
        ...(planPath ? { planPath } : {}),
        ...(params.plan ? { plan: params.plan } : {}),
        ...(params.executionMode ? { executionMode: params.executionMode } : {}),
        ...(executionManifestPath ? { executionManifestPath } : {}),
        ...(typeof params.maxSteps === "number" ? { maxSteps: params.maxSteps } : {}),
        ...(typeof params.allowBlockedDevSmoke === "boolean" ? { allowBlockedDevSmoke: params.allowBlockedDevSmoke } : {}),
        ...(typeof params.allowExecution === "boolean" ? { allowExecution: params.allowExecution } : {}),
        ...(params.backendConfig ? { backendConfig: params.backendConfig } : {}),
      });

      return toToolResponse(payloadFromBridge(artifactService, bridgeResult));
    },
  };
}
