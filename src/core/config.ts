import { Type } from "@sinclair/typebox";

import type { MaterialsConfigSource, MaterialsLabPluginConfig } from "../types/config.js";

export const DEFAULT_PLUGIN_CONFIG: MaterialsLabPluginConfig = {
  pythonPath: "python3",
  mpApiKey: "",
  workspaceRoot: "~/.openclaw/materials-lab",
  cacheDir: "",
  defaultBatchLimit: 20,
  enableAseTools: false,
};

export const PLUGIN_CONFIG_SCHEMA = Type.Object(
  {
    pythonPath: Type.String({ default: DEFAULT_PLUGIN_CONFIG.pythonPath, minLength: 1 }),
    mpApiKey: Type.String({ default: DEFAULT_PLUGIN_CONFIG.mpApiKey }),
    workspaceRoot: Type.String({ default: DEFAULT_PLUGIN_CONFIG.workspaceRoot, minLength: 1 }),
    cacheDir: Type.String({ default: DEFAULT_PLUGIN_CONFIG.cacheDir }),
    defaultBatchLimit: Type.Number({
      default: DEFAULT_PLUGIN_CONFIG.defaultBatchLimit,
      minimum: 1,
      maximum: 500,
    }),
    enableAseTools: Type.Boolean({ default: DEFAULT_PLUGIN_CONFIG.enableAseTools }),
  },
  { additionalProperties: false },
);

export function resolvePluginConfig(
  source: MaterialsConfigSource | undefined,
  pluginId: string,
  env: NodeJS.ProcessEnv = process.env,
): MaterialsLabPluginConfig {
  const rawConfig = source?.plugins?.entries?.[pluginId]?.config ?? {};

  return {
    pythonPath: rawConfig.pythonPath?.trim() || env.MATERIALS_LAB_PYTHON || DEFAULT_PLUGIN_CONFIG.pythonPath,
    mpApiKey: rawConfig.mpApiKey?.trim() || env.MATERIALS_PROJECT_API_KEY || DEFAULT_PLUGIN_CONFIG.mpApiKey,
    workspaceRoot:
      rawConfig.workspaceRoot?.trim() || env.MATERIALS_LAB_WORKSPACE_ROOT || DEFAULT_PLUGIN_CONFIG.workspaceRoot,
    cacheDir: rawConfig.cacheDir?.trim() || env.MATERIALS_LAB_CACHE_DIR || DEFAULT_PLUGIN_CONFIG.cacheDir,
    defaultBatchLimit: sanitizeBatchLimit(
      rawConfig.defaultBatchLimit ?? parseOptionalNumber(env.MATERIALS_LAB_DEFAULT_BATCH_LIMIT),
    ),
    enableAseTools: parseBoolean(rawConfig.enableAseTools, env.MATERIALS_LAB_ENABLE_ASE_TOOLS),
  };
}

function parseOptionalNumber(value: string | undefined): number | undefined {
  if (!value) {
    return undefined;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function sanitizeBatchLimit(value: number | undefined): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return DEFAULT_PLUGIN_CONFIG.defaultBatchLimit;
  }

  return Math.max(1, Math.min(500, Math.floor(value)));
}

function parseBoolean(configValue: boolean | undefined, envValue: string | undefined): boolean {
  if (typeof configValue === "boolean") {
    return configValue;
  }

  if (!envValue) {
    return DEFAULT_PLUGIN_CONFIG.enableAseTools;
  }

  return ["1", "true", "yes", "on"].includes(envValue.trim().toLowerCase());
}
