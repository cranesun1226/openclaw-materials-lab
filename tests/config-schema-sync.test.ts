import { readFile } from "node:fs/promises";

import { describe, expect, it } from "vitest";

import { DEFAULT_PLUGIN_CONFIG } from "../src/core/config.js";
import { PLUGIN_DESCRIPTION, PLUGIN_ID, PLUGIN_NAME } from "../src/core/runtime-context.js";

describe("plugin manifest sync", () => {
  it("keeps runtime constants and manifest defaults aligned", async () => {
    const manifestPath = new URL("../openclaw.plugin.json", import.meta.url);
    const manifest = JSON.parse(await readFile(manifestPath, "utf8")) as {
      id: string;
      name: string;
      description: string;
      configSchema: {
        additionalProperties: boolean;
        properties: Record<string, Record<string, unknown>>;
      };
      uiHints: Record<string, unknown>;
    };

    expect(manifest.id).toBe(PLUGIN_ID);
    expect(manifest.name).toBe(PLUGIN_NAME);
    expect(manifest.description).toBe(PLUGIN_DESCRIPTION);
    expect(manifest.configSchema.additionalProperties).toBe(false);
    expect(Object.keys(manifest.configSchema.properties).sort()).toEqual(
      ["cacheDir", "defaultBatchLimit", "enableAseTools", "mpApiKey", "pythonPath", "workspaceRoot"].sort(),
    );
    expect(Object.keys(manifest.uiHints).sort()).toEqual(
      ["cacheDir", "defaultBatchLimit", "enableAseTools", "mpApiKey", "pythonPath", "workspaceRoot"].sort(),
    );
    expect(manifest.configSchema.properties.pythonPath?.default).toBe(DEFAULT_PLUGIN_CONFIG.pythonPath);
    expect(manifest.configSchema.properties.mpApiKey?.default).toBe(DEFAULT_PLUGIN_CONFIG.mpApiKey);
    expect(manifest.configSchema.properties.workspaceRoot?.default).toBe(DEFAULT_PLUGIN_CONFIG.workspaceRoot);
    expect(manifest.configSchema.properties.cacheDir?.default).toBe(DEFAULT_PLUGIN_CONFIG.cacheDir);
    expect(manifest.configSchema.properties.defaultBatchLimit?.default).toBe(DEFAULT_PLUGIN_CONFIG.defaultBatchLimit);
    expect(manifest.configSchema.properties.defaultBatchLimit?.minimum).toBe(1);
    expect(manifest.configSchema.properties.defaultBatchLimit?.maximum).toBe(500);
    expect(manifest.configSchema.properties.enableAseTools?.default).toBe(DEFAULT_PLUGIN_CONFIG.enableAseTools);
  });
});
