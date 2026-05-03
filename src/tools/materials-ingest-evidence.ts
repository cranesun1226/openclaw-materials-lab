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

const IngestEvidenceSchema = Type.Object(
  {
    planPath: Type.Optional(Type.String({ minLength: 1 })),
    plan: Type.Optional(Type.Record(Type.String(), Type.Any())),
    candidateId: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
    parser: Type.Optional(
      Type.Union([
        Type.Literal("auto"),
        Type.Literal("quantum-espresso"),
        Type.Literal("vasp"),
        Type.Literal("literature-json"),
        Type.Literal("experiment-json"),
        Type.Literal("evidence-jsonl"),
        Type.Literal("csv"),
      ]),
    ),
    artifactPaths: Type.Optional(Type.Array(Type.String({ minLength: 1 }), { maxItems: 200 })),
    evidenceRows: Type.Optional(Type.Array(EvidenceRowSchema, { maxItems: 1000 })),
    evidenceRequirementId: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
    evidenceLedgerPath: Type.Optional(Type.String({ minLength: 1 })),
    outputLedgerPath: Type.Optional(Type.String({ minLength: 1 })),
    defaultStatus: Type.Optional(Type.String({ minLength: 1, maxLength: 120 })),
    sourceLabel: Type.Optional(Type.String({ minLength: 1, maxLength: 500 })),
  },
  { additionalProperties: false },
);

export type MaterialsIngestEvidenceParams = Static<typeof IngestEvidenceSchema>;

export function createMaterialsIngestEvidenceTool(context: MaterialsPluginContext): AnyAgentTool {
  return {
    name: "materials_ingest_evidence",
    label: "Ingest Evidence",
    description:
      "Parse QE/VASP/literature/experiment artifacts into evidence ledger rows for claim evaluation.",
    parameters: IngestEvidenceSchema,
    async execute(_callId, rawParams) {
      const params = rawParams as MaterialsIngestEvidenceParams;
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
      const artifactPaths = params.artifactPaths?.map((item) =>
        ensureWithinRoot(workspacePaths.workspaceRoot, item, "artifactPath"),
      );
      const artifactDir = ensureWithinRoot(
        workspacePaths.reportsDir,
        path.join(workspacePaths.reportsDir, "evidence-ingestion"),
        "evidence ingestion artifact dir",
      );
      const bridgeResult = await context.getBridge().ingestEvidence({
        artifactDir,
        ...(planPath ? { planPath } : {}),
        ...(params.plan ? { plan: params.plan } : {}),
        ...(params.candidateId ? { candidateId: params.candidateId } : {}),
        ...(params.parser ? { parser: params.parser } : {}),
        ...(artifactPaths ? { artifactPaths } : {}),
        ...(params.evidenceRows ? { evidenceRows: params.evidenceRows } : {}),
        ...(params.evidenceRequirementId ? { evidenceRequirementId: params.evidenceRequirementId } : {}),
        ...(evidenceLedgerPath ? { evidenceLedgerPath } : {}),
        ...(outputLedgerPath ? { outputLedgerPath } : {}),
        ...(params.defaultStatus ? { defaultStatus: params.defaultStatus } : {}),
        ...(params.sourceLabel ? { sourceLabel: params.sourceLabel } : {}),
      });

      return toToolResponse(payloadFromBridge(artifactService, bridgeResult));
    },
  };
}
