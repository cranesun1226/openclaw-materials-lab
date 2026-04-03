export interface MaterialsLogger {
  debug(message: string, meta?: unknown): void;
  info(message: string, meta?: unknown): void;
  warn(message: string, meta?: unknown): void;
  error(message: string, meta?: unknown): void;
}

interface LoggerLike {
  debug?: (message: string, meta?: unknown) => void;
  info?: (message: string, meta?: unknown) => void;
  warn?: (message: string, meta?: unknown) => void;
  error?: (message: string, meta?: unknown) => void;
}

function consoleLog(level: "debug" | "info" | "warn" | "error", message: string, meta?: unknown): void {
  const sink = console[level].bind(console);
  if (meta === undefined) {
    sink(message);
    return;
  }

  sink(message, meta);
}

export function createLogger(logger?: LoggerLike): MaterialsLogger {
  return {
    debug(message, meta) {
      logger?.debug?.(message, meta) ?? consoleLog("debug", message, meta);
    },
    info(message, meta) {
      logger?.info?.(message, meta) ?? consoleLog("info", message, meta);
    },
    warn(message, meta) {
      logger?.warn?.(message, meta) ?? consoleLog("warn", message, meta);
    },
    error(message, meta) {
      logger?.error?.(message, meta) ?? consoleLog("error", message, meta);
    },
  };
}
