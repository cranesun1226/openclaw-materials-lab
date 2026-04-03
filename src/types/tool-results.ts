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

export interface OpenClawToolResponse<TData = unknown> {
  content: Array<{ type: "text"; text: string }>;
  structuredContent: ToolPayload<TData>;
}

export function toToolResponse<TData>(payload: ToolPayload<TData>): OpenClawToolResponse<TData> {
  return {
    content: [{ type: "text", text: payload.summary }],
    structuredContent: payload,
  };
}
