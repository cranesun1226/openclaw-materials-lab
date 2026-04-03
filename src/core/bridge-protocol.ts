import { randomUUID } from "node:crypto";

import type { BridgeAction, BridgeRequest, BridgeResponse, BridgeSuccess } from "../types/bridge.js";
import { PythonBridgeError } from "./errors.js";

export function createBridgeRequest<TPayload>(action: BridgeAction, payload: TPayload): BridgeRequest<TPayload> {
  return {
    action,
    requestId: randomUUID(),
    payload,
  };
}

export function parseBridgeResponse<TData>(raw: string, stderr = ""): BridgeSuccess<TData> {
  let parsed: BridgeResponse<TData>;

  try {
    parsed = JSON.parse(raw) as BridgeResponse<TData>;
  } catch (error) {
    throw new PythonBridgeError("Python worker returned invalid JSON.", {
      hint: "Run `openclaw materials doctor` to inspect Python worker health.",
      stderr,
      cause: error,
      details: { raw },
    });
  }

  if (!parsed || typeof parsed !== "object") {
    throw new PythonBridgeError("Python worker returned an empty response.", {
      stderr,
    });
  }

  if (parsed.ok) {
    return parsed;
  }

  throw new PythonBridgeError(parsed.error.message, {
    ...(parsed.error.hint ? { hint: parsed.error.hint } : {}),
    ...(parsed.error.details !== undefined ? { details: parsed.error.details } : {}),
    ...((parsed.error.stderr ?? stderr) ? { stderr: parsed.error.stderr ?? stderr } : {}),
  });
}
