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

const EvidenceRequirementSchema = Type.Object(
  {
    id: Type.Optional(Type.String({ minLength: 1, maxLength: 80 })),
    label: Type.String({ minLength: 1, maxLength: 160 }),
    description: Type.Optional(Type.String({ minLength: 1, maxLength: 800 })),
    propertyKeys: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 80 }), { maxItems: 20 })),
    evidenceTypes: Type.Optional(
      Type.Array(
        Type.Union([
          Type.Literal("database"),
          Type.Literal("literature"),
          Type.Literal("dft"),
          Type.Literal("dfpt"),
          Type.Literal("md"),
          Type.Literal("workflow"),
          Type.Literal("experiment"),
          Type.Literal("safety"),
        ]),
        { maxItems: 12 },
      ),
    ),
    acceptanceCriteria: Type.Optional(Type.String({ minLength: 1, maxLength: 500 })),
    requiredForClaim: Type.Optional(Type.Boolean()),
  },
  { additionalProperties: true },
);

const CandidateGenerationSchema = Type.Object(
  {
    strategy: Type.Optional(Type.String({ minLength: 1, maxLength: 500 })),
    autoDiscover: Type.Optional(Type.Boolean()),
    discoverAdditionalCandidates: Type.Optional(Type.Boolean()),
    allowDevelopmentFixtures: Type.Optional(Type.Boolean()),
    maxQueries: Type.Optional(Type.Number({ minimum: 1, maximum: 30 })),
    perQueryLimit: Type.Optional(Type.Number({ minimum: 1, maximum: 100 })),
    seedMaterials: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 80 }), { maxItems: 100 })),
    elementsInclude: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 3 }), { maxItems: 40 })),
    elementsExclude: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 3 }), { maxItems: 40 })),
    formulas: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 80 }), { maxItems: 100 })),
    databaseQueries: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 300 }), { maxItems: 30 })),
    literatureQueries: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 300 }), { maxItems: 30 })),
  },
  { additionalProperties: true },
);

const PlanResearchLoopSchema = Type.Object(
  {
    candidates: Type.Optional(Type.Array(PlanCandidateSchema, { minItems: 0, maxItems: 50 })),
    researchGoal: Type.Optional(Type.String({ minLength: 1, maxLength: 1000 })),
    targetApplication: Type.Optional(Type.String({ minLength: 1, maxLength: 300 })),
    hypothesis: Type.Optional(Type.String({ minLength: 1, maxLength: 1000 })),
    constraints: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 300 }), { maxItems: 50 })),
    literatureQueries: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 300 }), { maxItems: 30 })),
    databaseQueries: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 300 }), { maxItems: 30 })),
    evidenceRequirements: Type.Optional(Type.Array(EvidenceRequirementSchema, { maxItems: 50 })),
    validationMethods: Type.Optional(
      Type.Array(
        Type.Union([
          Type.Literal("database"),
          Type.Literal("literature"),
          Type.Literal("dft"),
          Type.Literal("dfpt"),
          Type.Literal("md"),
          Type.Literal("workflow"),
          Type.Literal("experiment"),
          Type.Literal("safety"),
        ]),
        { maxItems: 20 },
      ),
    ),
    candidateGeneration: Type.Optional(CandidateGenerationSchema),
    autonomyMode: Type.Optional(
      Type.Union([
        Type.Literal("bounded"),
        Type.Literal("high-autonomy-plan"),
        Type.Literal("human-gated"),
      ]),
    ),
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
    label: "Compile Research Protocol",
    description: "Compile an approval-gated dynamic materials research protocol from a goal, constraints, evidence requirements, and optional candidates.",
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
        candidates: (params.candidates ?? []) as ComparedCandidate[],
        artifactDir,
        ...(params.researchGoal ? { researchGoal: params.researchGoal } : {}),
        ...(params.targetApplication ? { targetApplication: params.targetApplication } : {}),
        ...(params.hypothesis ? { hypothesis: params.hypothesis } : {}),
        ...(params.constraints ? { constraints: params.constraints } : {}),
        ...(params.literatureQueries ? { literatureQueries: params.literatureQueries } : {}),
        ...(params.databaseQueries ? { databaseQueries: params.databaseQueries } : {}),
        ...(params.evidenceRequirements ? { evidenceRequirements: params.evidenceRequirements } : {}),
        ...(params.validationMethods ? { validationMethods: params.validationMethods } : {}),
        ...(params.candidateGeneration ? { candidateGeneration: params.candidateGeneration } : {}),
        ...(params.autonomyMode ? { autonomyMode: params.autonomyMode } : {}),
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
