import path from "node:path";

import type { ArtifactService } from "../services/artifact-service.js";
import { formatErrorForTool } from "../core/errors.js";
import type { BridgeSuccess } from "../types/bridge.js";
import type { ToolArtifact, ToolPayload } from "../types/tool-results.js";

export function payloadFromBridge<TData>(
  artifactService: ArtifactService,
  bridgeResult: BridgeSuccess<TData>,
  extraArtifacts: string[] = [],
): ToolPayload<TData> {
  const artifacts = [
    ...(bridgeResult.artifacts ?? []).map((artifactPath) => artifactService.describePath(artifactPath)),
    ...extraArtifacts.map((artifactPath) => artifactService.describePath(artifactPath)),
  ];

  return {
    summary: bridgeResult.summary,
    data: bridgeResult.data,
    artifacts,
    warnings: bridgeResult.warnings ?? [],
  };
}

export function singleArtifactPayload<TData>(
  summary: string,
  data: TData,
  artifact: ToolArtifact,
  warnings: string[] = [],
): ToolPayload<TData> {
  return {
    summary,
    data,
    artifacts: [artifact],
    warnings,
  };
}

export function asStructuredToolError(error: unknown): never {
  throw new Error(formatErrorForTool(error));
}

export function ensureArray<T>(value: T[] | undefined): T[] {
  return value ?? [];
}

export function basenameOrValue(value: string): string {
  return path.basename(value) || value;
}
