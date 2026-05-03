import path from "node:path";

import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool } from "openclaw/plugin-sdk/plugin-entry";

import { ensureWithinRoot } from "../core/paths.js";
import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { toToolResponse } from "../types/tool-results.js";
import { payloadFromBridge } from "./shared.js";

const SearchLiteratureSchema = Type.Object(
  {
    planPath: Type.Optional(Type.String({ minLength: 1 })),
    plan: Type.Optional(Type.Record(Type.String(), Type.Any())),
    candidateId: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
    queries: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 500 }), { maxItems: 30 })),
    query: Type.Optional(Type.String({ minLength: 1, maxLength: 500 })),
    researchGoal: Type.Optional(Type.String({ minLength: 1, maxLength: 1000 })),
    providers: Type.Optional(Type.Array(Type.Union([Type.Literal("openalex"), Type.Literal("crossref")]), { maxItems: 2 })),
    maxResultsPerQuery: Type.Optional(Type.Number({ minimum: 1, maximum: 25 })),
    timeoutSeconds: Type.Optional(Type.Number({ minimum: 2, maximum: 60 })),
    allowNetwork: Type.Optional(Type.Boolean()),
    allowDevelopmentFixtures: Type.Optional(Type.Boolean()),
    evidenceRequirementId: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
    evidenceLedgerPath: Type.Optional(Type.String({ minLength: 1 })),
    outputLedgerPath: Type.Optional(Type.String({ minLength: 1 })),
    sourceLabel: Type.Optional(Type.String({ minLength: 1, maxLength: 500 })),
  },
  { additionalProperties: false },
);

export type MaterialsSearchLiteratureParams = Static<typeof SearchLiteratureSchema>;

export function createMaterialsSearchLiteratureTool(context: MaterialsPluginContext): AnyAgentTool {
  return {
    name: "materials_search_literature",
    label: "Search Literature Evidence",
    description:
      "Search public literature metadata providers and convert citation provenance into evidence-ledger rows.",
    parameters: SearchLiteratureSchema,
    async execute(_callId, rawParams) {
      const params = rawParams as MaterialsSearchLiteratureParams;
      const artifactService = context.getArtifactService();
      const workspacePaths = artifactService.getPaths();
      await artifactService.ensureReady();

      const planPath = params.planPath
        ? ensureWithinRoot(workspacePaths.workspaceRoot, params.planPath, "planPath")
        : undefined;
      const evidenceLedgerPath = params.evidenceLedgerPath
        ? ensureWithinRoot(workspacePaths.workspaceRoot, params.evidenceLedgerPath, "evidenceLedgerPath")
        : undefined;
      const outputLedgerPath = params.outputLedgerPath
        ? ensureWithinRoot(workspacePaths.workspaceRoot, params.outputLedgerPath, "outputLedgerPath")
        : undefined;
      const artifactDir = ensureWithinRoot(
        workspacePaths.reportsDir,
        path.join(workspacePaths.reportsDir, "literature-evidence-search"),
        "literature search artifact dir",
      );
      const bridgeResult = await context.getBridge().searchLiterature({
        artifactDir,
        ...(planPath ? { planPath } : {}),
        ...(params.plan ? { plan: params.plan } : {}),
        ...(params.candidateId ? { candidateId: params.candidateId } : {}),
        ...(params.queries ? { queries: params.queries } : {}),
        ...(params.query ? { query: params.query } : {}),
        ...(params.researchGoal ? { researchGoal: params.researchGoal } : {}),
        ...(params.providers ? { providers: params.providers } : {}),
        ...(typeof params.maxResultsPerQuery === "number" ? { maxResultsPerQuery: params.maxResultsPerQuery } : {}),
        ...(typeof params.timeoutSeconds === "number" ? { timeoutSeconds: params.timeoutSeconds } : {}),
        ...(typeof params.allowNetwork === "boolean" ? { allowNetwork: params.allowNetwork } : {}),
        ...(typeof params.allowDevelopmentFixtures === "boolean"
          ? { allowDevelopmentFixtures: params.allowDevelopmentFixtures }
          : {}),
        ...(params.evidenceRequirementId ? { evidenceRequirementId: params.evidenceRequirementId } : {}),
        ...(evidenceLedgerPath ? { evidenceLedgerPath } : {}),
        ...(outputLedgerPath ? { outputLedgerPath } : {}),
        ...(params.sourceLabel ? { sourceLabel: params.sourceLabel } : {}),
      });

      return toToolResponse(payloadFromBridge(artifactService, bridgeResult));
    },
  };
}
