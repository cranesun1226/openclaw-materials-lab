import type { AgentToolResult } from "@mariozechner/pi-agent-core";

export interface ToolArtifact {
  label: string;
  path: string;
  kind: "structure" | "plot" | "note" | "report" | "json" | "text" | "other";
}

export interface ToolPayload<TData = unknown> {
  summary: string;
  data: TData;
  artifacts: ToolArtifact[];
  warnings: string[];
}

export type MaterialsToolResponse<TData = unknown> = AgentToolResult<ToolPayload<TData>> & {
  structuredContent: ToolPayload<TData>;
};

export function toToolResponse<TData>(payload: ToolPayload<TData>): MaterialsToolResponse<TData> {
  return {
    content: [{ type: "text", text: payload.summary }],
    details: payload,
    structuredContent: payload,
  };
}
