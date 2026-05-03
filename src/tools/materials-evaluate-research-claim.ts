import path from "node:path";

import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool } from "openclaw/plugin-sdk/plugin-entry";

import { ensureWithinRoot } from "../core/paths.js";
import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { toToolResponse } from "../types/tool-results.js";
import { payloadFromBridge } from "./shared.js";

const EvidenceRowSchema = Type.Object(
  {
    candidateId: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
    formula: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
    evidenceRequirementId: Type.String({ minLength: 1, maxLength: 120 }),
    claim: Type.Optional(Type.String({ minLength: 1, maxLength: 1000 })),
    status: Type.String({ minLength: 1, maxLength: 120 }),
    sourceType: Type.String({ minLength: 1, maxLength: 120 }),
    source: Type.Optional(Type.String({ minLength: 1, maxLength: 500 })),
    confidence: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
    propertyValues: Type.Optional(Type.Record(Type.String(), Type.Any())),
    artifactPath: Type.Optional(Type.String({ minLength: 1 })),
    sourcePath: Type.Optional(Type.String({ minLength: 1 })),
    citation: Type.Optional(Type.String({ minLength: 1, maxLength: 1000 })),
    queryIds: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 120 }), { maxItems: 100 })),
  },
  { additionalProperties: true },
);

const EvaluateResearchClaimSchema = Type.Object(
  {
    planPath: Type.Optional(Type.String({ minLength: 1 })),
    plan: Type.Optional(Type.Record(Type.String(), Type.Any())),
    evidenceLedgerPath: Type.Optional(Type.String({ minLength: 1 })),
    evidenceRows: Type.Optional(Type.Array(EvidenceRowSchema, { maxItems: 1000 })),
    candidateId: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
    requestedClaimLevel: Type.Optional(
      Type.Union([
        Type.Literal("candidate-hypothesis"),
        Type.Literal("proxy-shortlist"),
        Type.Literal("property-backed-shortlist"),
        Type.Literal("research-grade-candidate"),
      ]),
    ),
  },
  { additionalProperties: false },
);

export type MaterialsEvaluateResearchClaimParams = Static<typeof EvaluateResearchClaimSchema>;

export function createMaterialsEvaluateResearchClaimTool(context: MaterialsPluginContext): AnyAgentTool {
  return {
    name: "materials_evaluate_research_claim",
    label: "Evaluate Research Claim",
    description:
      "Evaluate whether a candidate's evidence ledger satisfies the compiled claim policy and emit a claim-review artifact.",
    parameters: EvaluateResearchClaimSchema,
    async execute(_callId, rawParams) {
      const params = rawParams as MaterialsEvaluateResearchClaimParams;
      const artifactService = context.getArtifactService();
      const workspacePaths = artifactService.getPaths();
      await artifactService.ensureReady();

      const planPath = params.planPath
        ? ensureWithinRoot(workspacePaths.workspaceRoot, params.planPath, "planPath")
        : undefined;
      const evidenceLedgerPath = params.evidenceLedgerPath
        ? ensureWithinRoot(workspacePaths.workspaceRoot, params.evidenceLedgerPath, "evidenceLedgerPath")
        : undefined;
      const artifactDir = ensureWithinRoot(
        workspacePaths.reportsDir,
        path.join(workspacePaths.reportsDir, "claim-reviews"),
        "claim review artifact dir",
      );
      const bridgeResult = await context.getBridge().evaluateResearchClaim({
        artifactDir,
        ...(planPath ? { planPath } : {}),
        ...(params.plan ? { plan: params.plan } : {}),
        ...(evidenceLedgerPath ? { evidenceLedgerPath } : {}),
        ...(params.evidenceRows ? { evidenceRows: params.evidenceRows } : {}),
        ...(params.candidateId ? { candidateId: params.candidateId } : {}),
        ...(params.requestedClaimLevel ? { requestedClaimLevel: params.requestedClaimLevel } : {}),
      });

      return toToolResponse(payloadFromBridge(artifactService, bridgeResult));
    },
  };
}
