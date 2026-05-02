import { runCommandWithTimeout } from "openclaw/plugin-sdk/process-runtime";

const DEFAULT_PROCESS_TIMEOUT_MS = 10 * 60_000;

export interface ProcessRunResult {
  code: number | null;
  stdout: string;
  stderr: string;
}

export interface ProcessRunOptions {
  cwd?: string;
  env?: NodeJS.ProcessEnv;
  timeoutMs?: number;
}

export type ProcessRunner = (
  command: string,
  args: string[],
  options?: ProcessRunOptions,
) => Promise<ProcessRunResult>;

export const defaultProcessRunner: ProcessRunner = async (command, args, options) => {
  const commandOptions: { timeoutMs: number; cwd?: string; env?: NodeJS.ProcessEnv } = {
    timeoutMs: options?.timeoutMs ?? DEFAULT_PROCESS_TIMEOUT_MS,
  };

  if (options?.cwd) {
    commandOptions.cwd = options.cwd;
  }

  if (options?.env) {
    commandOptions.env = options.env;
  }

  const result = await runCommandWithTimeout([command, ...args], commandOptions);

  return {
    code: result.code,
    stdout: result.stdout,
    stderr: result.stderr,
  };
};
