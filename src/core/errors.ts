import type { BridgeErrorDetails } from "../types/bridge.js";

export class MaterialsLabError extends Error {
  public readonly code: string;
  public readonly hint: string | undefined;
  public readonly details: unknown | undefined;

  public constructor(code: string, message: string, options?: { hint?: string; details?: unknown; cause?: unknown }) {
    super(message, { cause: options?.cause });
    this.name = this.constructor.name;
    this.code = code;
    this.hint = options?.hint;
    this.details = options?.details;
  }
}

export class ConfigurationError extends MaterialsLabError {
  public constructor(message: string, options?: { hint?: string; details?: unknown; cause?: unknown }) {
    super("CONFIGURATION_ERROR", message, options);
  }
}

export class PathValidationError extends MaterialsLabError {
  public constructor(message: string, options?: { hint?: string; details?: unknown; cause?: unknown }) {
    super("PATH_VALIDATION_ERROR", message, options);
  }
}

export class PythonBridgeError extends MaterialsLabError {
  public readonly stderr: string | undefined;

  public constructor(message: string, options?: { hint?: string; details?: unknown; cause?: unknown; stderr?: string }) {
    super("PYTHON_BRIDGE_ERROR", message, options);
    this.stderr = options?.stderr;
  }
}

export function bridgeErrorToException(error: BridgeErrorDetails): PythonBridgeError {
  return new PythonBridgeError(error.message, {
    ...(error.hint ? { hint: error.hint } : {}),
    ...(error.details !== undefined ? { details: error.details } : {}),
    ...(error.stderr ? { stderr: error.stderr } : {}),
  });
}

export function formatErrorForTool(error: unknown): string {
  if (error instanceof MaterialsLabError) {
    return error.hint ? `${error.message} Hint: ${error.hint}` : error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unknown Materials Lab error.";
}
