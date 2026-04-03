import type { OpenClawPluginApi } from "openclaw/plugin-sdk/plugin-entry";

const APPROVAL_REQUIRED_TOOLS = new Set(["materials_ase_relax", "materials_batch_screen"]);

export function registerMaterialsApprovalHook(api: OpenClawPluginApi): void {
  api.on("before_tool_call", (event) => {
    const toolName = extractToolName(event);
    if (!toolName || !APPROVAL_REQUIRED_TOOLS.has(toolName)) {
      return undefined;
    }

    return {
      requireApproval: {
        title: `Approve ${toolName}`,
        description: `${toolName} can run heavier local computation and may write multiple artifacts under the Materials Lab workspace.`,
        severity: "warning",
      },
    };
  });
}

function extractToolName(context: unknown): string | undefined {
  if (!context || typeof context !== "object") {
    return undefined;
  }

  const record = context as Record<string, unknown>;
  if (typeof record.toolName === "string") {
    return record.toolName;
  }

  const tool = record.tool;
  if (tool && typeof tool === "object" && typeof (tool as Record<string, unknown>).name === "string") {
    return (tool as Record<string, string>).name;
  }

  if (typeof record.name === "string") {
    return record.name;
  }

  return undefined;
}
