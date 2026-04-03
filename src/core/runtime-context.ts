import type { OpenClawPluginApi } from "openclaw/plugin-sdk/plugin-entry";

import { resolvePluginConfig } from "./config.js";
import { createLogger, type MaterialsLogger } from "./logger.js";
import { resolveWorkspacePaths } from "./paths.js";
import { ArtifactService } from "../services/artifact-service.js";
import { NoteService } from "../services/note-service.js";
import { PythonBridgeService } from "../services/python-bridge.js";
import type { MaterialsConfigSource, MaterialsLabPluginConfig, MaterialsWorkspacePaths } from "../types/config.js";

export const PLUGIN_ID = "materials-lab";
export const PLUGIN_NAME = "Materials Lab";
export const PLUGIN_DESCRIPTION = "Autonomous materials-science research tools and local Python workflows for OpenClaw.";

export interface MaterialsPluginContext {
  logger: MaterialsLogger;
  loadConfigSource(): MaterialsConfigSource | undefined;
  resolveConfig(overrides?: Partial<MaterialsLabPluginConfig>): MaterialsLabPluginConfig;
  resolvePaths(overrides?: Partial<MaterialsLabPluginConfig>): MaterialsWorkspacePaths;
  getArtifactService(overrides?: Partial<MaterialsLabPluginConfig>): ArtifactService;
  getNoteService(overrides?: Partial<MaterialsLabPluginConfig>): NoteService;
  getBridge(overrides?: Partial<MaterialsLabPluginConfig>): PythonBridgeService;
  warmup(): Promise<void>;
  stop(): Promise<void>;
}

export function createPluginContext(api: OpenClawPluginApi): MaterialsPluginContext {
  const logger = createLogger(api.logger);
  let defaultArtifactService: ArtifactService | undefined;
  let defaultNoteService: NoteService | undefined;
  let defaultBridge: PythonBridgeService | undefined;

  const loadConfigSource = (): MaterialsConfigSource | undefined => {
    const loader = api.runtime?.config?.loadConfig;
    if (typeof loader !== "function") {
      return undefined;
    }

    return loader() as MaterialsConfigSource | undefined;
  };

  const resolveConfigWithOverrides = (overrides?: Partial<MaterialsLabPluginConfig>): MaterialsLabPluginConfig => ({
    ...resolvePluginConfig(loadConfigSource(), PLUGIN_ID),
    ...sanitizeOverrides(overrides),
  });

  const resolvePathsWithOverrides = (overrides?: Partial<MaterialsLabPluginConfig>): MaterialsWorkspacePaths =>
    resolveWorkspacePaths(resolveConfigWithOverrides(overrides));

  const createArtifactServiceFor = (overrides?: Partial<MaterialsLabPluginConfig>): ArtifactService =>
    new ArtifactService(resolvePathsWithOverrides(overrides));

  const createNoteServiceFor = (overrides?: Partial<MaterialsLabPluginConfig>): NoteService =>
    new NoteService(createArtifactServiceFor(overrides));

  const createBridgeFor = (overrides?: Partial<MaterialsLabPluginConfig>): PythonBridgeService =>
    new PythonBridgeService(resolveConfigWithOverrides(overrides), resolvePathsWithOverrides(overrides), logger);

  return {
    logger,
    loadConfigSource,
    resolveConfig(overrides) {
      return resolveConfigWithOverrides(overrides);
    },
    resolvePaths(overrides) {
      return resolvePathsWithOverrides(overrides);
    },
    getArtifactService(overrides) {
      if (overrides) {
        return createArtifactServiceFor(overrides);
      }

      defaultArtifactService ??= createArtifactServiceFor();
      return defaultArtifactService;
    },
    getNoteService(overrides) {
      if (overrides) {
        return createNoteServiceFor(overrides);
      }

      defaultNoteService ??= createNoteServiceFor();
      return defaultNoteService;
    },
    getBridge(overrides) {
      if (overrides) {
        return createBridgeFor(overrides);
      }

      defaultBridge ??= createBridgeFor();
      return defaultBridge;
    },
    async warmup() {
      try {
        await this.getArtifactService().ensureReady();
        await this.getBridge().warmup();
      } catch (error) {
        logger.warn("Materials Lab warmup encountered a recoverable issue.", {
          error: error instanceof Error ? error.message : String(error),
        });
      }
    },
    async stop() {
      await defaultBridge?.stop();
    },
  };
}

function sanitizeOverrides(
  overrides: Partial<MaterialsLabPluginConfig> | undefined,
): Partial<MaterialsLabPluginConfig> | undefined {
  if (!overrides) {
    return undefined;
  }

  const sanitized: Partial<MaterialsLabPluginConfig> = {};

  if (typeof overrides.pythonPath === "string" && overrides.pythonPath.trim()) {
    sanitized.pythonPath = overrides.pythonPath.trim();
  }

  if (typeof overrides.mpApiKey === "string") {
    sanitized.mpApiKey = overrides.mpApiKey;
  }

  if (typeof overrides.workspaceRoot === "string" && overrides.workspaceRoot.trim()) {
    sanitized.workspaceRoot = overrides.workspaceRoot.trim();
  }

  if (typeof overrides.cacheDir === "string") {
    sanitized.cacheDir = overrides.cacheDir.trim();
  }

  if (typeof overrides.defaultBatchLimit === "number") {
    sanitized.defaultBatchLimit = overrides.defaultBatchLimit;
  }

  if (typeof overrides.enableAseTools === "boolean") {
    sanitized.enableAseTools = overrides.enableAseTools;
  }

  return Object.keys(sanitized).length > 0 ? sanitized : undefined;
}
