import path from "node:path";

import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool } from "openclaw/plugin-sdk/plugin-entry";

import { ensureWithinRoot } from "../core/paths.js";
import type { MaterialsPluginContext } from "../core/runtime-context.js";
import type { ComparedCandidate } from "../types/bridge.js";
import { toToolResponse } from "../types/tool-results.js";
import { payloadFromBridge } from "./shared.js";

const PlanCandidateSchema = Type.Object(
  {
    materialId: Type.String({ minLength: 1, maxLength: 80 }),
    formula: Type.String({ minLength: 1, maxLength: 80 }),
    source: Type.Optional(Type.Union([Type.Literal("materials-project"), Type.Literal("dev-fixture")])),
    score: Type.Optional(Type.Number()),
    primaryScore: Type.Optional(Type.Number()),
    secondaryScore: Type.Optional(Type.Number()),
    domainEvidenceScore: Type.Optional(Type.Number()),
    riskPenalty: Type.Optional(Type.Number()),
    rank: Type.Optional(Type.Number({ minimum: 1 })),
    rawRank: Type.Optional(Type.Number({ minimum: 1 })),
    family: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
    energyAboveHullEv: Type.Optional(Type.Number({ minimum: 0 })),
    bandGapEv: Type.Optional(Type.Number({ minimum: 0 })),
    densityGcm3: Type.Optional(Type.Number({ minimum: 0 })),
    materialsProjectUrl: Type.Optional(Type.String({ minLength: 1, maxLength: 300 })),
    domainEvidence: Type.Optional(Type.Record(Type.String(), Type.Any())),
    riskProfile: Type.Optional(Type.Record(Type.String(), Type.Any())),
    compositionDescriptors: Type.Optional(Type.Record(Type.String(), Type.Any())),
  },
  { additionalProperties: true },
);

const CriteriaSchema = Type.Object(
  {
    preset: Type.Optional(
      Type.Union([
        Type.Literal("generic"),
        Type.Literal("solid-electrolyte"),
        Type.Literal("high-k-dielectric"),
        Type.Literal("photovoltaic-absorber"),
        Type.Literal("thermoelectric"),
      ]),
    ),
    screeningLevel: Type.Optional(
      Type.Union([
        Type.Literal("technical-smoke"),
        Type.Literal("proxy-screen"),
        Type.Literal("property-backed-screen"),
        Type.Literal("research-shortlist"),
        Type.Literal("closed-loop-plan"),
        Type.Literal("validated-candidate"),
      ]),
    ),
    evidenceWeight: Type.Optional(Type.Number({ minimum: 0, maximum: 0.35 })),
  },
  { additionalProperties: true },
);

const BudgetSchema = Type.Object(
  {
    maxCandidates: Type.Optional(Type.Number({ minimum: 1, maximum: 50 })),
    maxCalculations: Type.Optional(Type.Number({ minimum: 1, maximum: 500 })),
    maxWallTimeHours: Type.Optional(Type.Number({ minimum: 0.25, maximum: 10000 })),
    computeBudgetUsd: Type.Optional(Type.Number({ minimum: 0 })),
    maxLoopIterations: Type.Optional(Type.Number({ minimum: 1, maximum: 20 })),
    allowExpensiveCalculations: Type.Optional(Type.Boolean()),
  },
  { additionalProperties: false },
);

const PlanResearchLoopSchema = Type.Object(
  {
    candidates: Type.Array(PlanCandidateSchema, { minItems: 1, maxItems: 50 }),
    criteria: Type.Optional(CriteriaSchema),
    objective: Type.Optional(Type.String({ minLength: 1, maxLength: 500 })),
    mode: Type.Optional(Type.Union([Type.Literal("property-backed"), Type.Literal("closed-loop")])),
    approvalPolicy: Type.Optional(Type.Union([Type.Literal("plan-only"), Type.Literal("approval-required")])),
    budget: Type.Optional(BudgetSchema),
  },
  { additionalProperties: false },
);

export type MaterialsPlanResearchLoopParams = Static<typeof PlanResearchLoopSchema>;

export function createMaterialsPlanResearchLoopTool(
  context: MaterialsPluginContext,
): AnyAgentTool {
  return {
    name: "materials_plan_research_loop",
    label: "Plan Research Loop",
    description: "Create an approval-gated property-backed research plan from ranked candidates.",
    parameters: PlanResearchLoopSchema,
    async execute(_callId, rawParams) {
      const params = rawParams as MaterialsPlanResearchLoopParams;
      const artifactService = context.getArtifactService();
      const workspacePaths = artifactService.getPaths();
      await artifactService.ensureReady();

      const artifactDir = ensureWithinRoot(
        workspacePaths.reportsDir,
        path.join(workspacePaths.reportsDir, "research-loop-plans"),
        "research loop artifact dir",
      );
      const bridgeResult = await context.getBridge().planResearchLoop({
        candidates: params.candidates as ComparedCandidate[],
        artifactDir,
        ...(params.criteria ? { criteria: params.criteria } : {}),
        ...(params.objective ? { objective: params.objective } : {}),
        ...(params.mode ? { mode: params.mode } : {}),
        ...(params.approvalPolicy ? { approvalPolicy: params.approvalPolicy } : {}),
        ...(params.budget ? { budget: params.budget } : {}),
      });

      return toToolResponse(payloadFromBridge(artifactService, bridgeResult));
    },
  };
}
