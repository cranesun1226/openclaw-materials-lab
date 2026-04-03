import { describe, expect, it } from "vitest";

import { registerMaterialsApprovalHook } from "../src/hooks/approvals.js";

describe("approval hooks", () => {
  it("requires approval for heavy tools only", () => {
    let handler: ((event: unknown) => unknown) | undefined;

    registerMaterialsApprovalHook({
      on(event, callback) {
        expect(event).toBe("before_tool_call");
        handler = callback as (event: unknown) => unknown;
      },
    } as Parameters<typeof registerMaterialsApprovalHook>[0]);

    expect(handler).toBeTypeOf("function");

    expect(handler?.({ toolName: "materials_search_mp", params: {} })).toBeUndefined();
    expect(handler?.({ toolName: "materials_batch_screen", params: {} })).toEqual({
      requireApproval: {
        title: "Approve materials_batch_screen",
        description:
          "materials_batch_screen can run heavier local computation and may write multiple artifacts under the Materials Lab workspace.",
        severity: "warning",
      },
    });
  });
});
