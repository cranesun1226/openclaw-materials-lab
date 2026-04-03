import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { afterEach, describe, expect, it, vi } from "vitest";

import { resolveWorkspacePaths } from "../src/core/paths.js";
import { createLogger } from "../src/core/logger.js";
import type { MaterialsPluginContext } from "../src/core/runtime-context.js";
import { ArtifactService } from "../src/services/artifact-service.js";
import { NoteService } from "../src/services/note-service.js";
import { runDoctor } from "../src/cli/doctor.js";
import { runSetupPython } from "../src/cli/setup-python.js";
import { runStatus } from "../src/cli/status.js";
import type { MaterialsLabPluginConfig, MaterialsWorkspacePaths } from "../src/types/config.js";

describe("CLI helpers", () => {
  const tempDirs: string[] = [];

  afterEach(async () => {
    await Promise.all(tempDirs.map(async (dir) => rm(dir, { recursive: true, force: true })));
    tempDirs.length = 0;
  });

  it("runs doctor checks against the resolved config", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-doctor-"));
    tempDirs.push(tempDir);
    const context = createTestContext(tempDir);
    const runner = vi
      .fn()
      .mockResolvedValueOnce({ code: 0, stdout: "Python 3.12.0", stderr: "" });

    const report = await runDoctor(context, {}, runner);

    expect(report.checks.find((check) => check.id === "python-available")?.status).toBe("ok");
    expect(report.checks.find((check) => check.id === "workspace-writable")?.status).toBe("ok");
    expect(report.checks.find((check) => check.id === "worker-health")?.status).toBe("ok");
    expect(report.checks.find((check) => check.id === "mp-api-key")?.status).toBe("warn");
    expect(runner).toHaveBeenCalledWith("python3", ["--version"]);
  });

  it("builds the setup-python command plan with the expected interpreter paths", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-setup-"));
    tempDirs.push(tempDir);
    const context = createTestContext(tempDir);
    const targetPath = path.join(tempDir, ".venv");
    const runner = vi.fn().mockResolvedValue({ code: 0, stdout: "", stderr: "" });

    const report = await runSetupPython(context, { targetPath }, runner);

    expect(report.venvPath).toBe(targetPath);
    expect(report.interpreterPath.endsWith(path.join(".venv", "bin", "python"))).toBe(true);
    expect(runner).toHaveBeenNthCalledWith(1, "python3", ["-m", "venv", targetPath]);
    expect(runner).toHaveBeenNthCalledWith(
      2,
      report.interpreterPath,
      ["-m", "pip", "install", "-r", report.requirementsPath],
    );
  });

  it("reports effective status and optional tool availability", async () => {
    const tempDir = await mkdtemp(path.join(os.tmpdir(), "materials-lab-status-"));
    tempDirs.push(tempDir);
    const context = createTestContext(tempDir, {
      enableAseTools: true,
      mpApiKey: "configured",
      source: {
        tools: {
          allow: ["materials_batch_screen", "materials_ase_relax"],
        },
      },
    });

    const report = runStatus(context);

    expect(report.config.hasMpApiKey).toBe(true);
    expect(report.tools.materials_ase_relax).toContain("enabled");
    expect(report.tools.materials_batch_screen).toContain("enabled");
  });
});

function createTestContext(
  tempDir: string,
  overrides?: Partial<MaterialsLabPluginConfig> & {
    source?: { tools?: { allow?: string[] } };
  },
): MaterialsPluginContext {
  const baseConfig: MaterialsLabPluginConfig = {
    pythonPath: "python3",
    mpApiKey: "",
    workspaceRoot: tempDir,
    cacheDir: path.join(tempDir, "cache"),
    defaultBatchLimit: 20,
    enableAseTools: false,
  };

  const source = overrides?.source ?? {};
  const configOverrides: Partial<MaterialsLabPluginConfig> = { ...overrides };
  delete (configOverrides as { source?: unknown }).source;
  const resolveConfig = (localOverrides?: Partial<MaterialsLabPluginConfig>): MaterialsLabPluginConfig => ({
    ...baseConfig,
    ...configOverrides,
    ...localOverrides,
    workspaceRoot: localOverrides?.workspaceRoot ?? overrides?.workspaceRoot ?? baseConfig.workspaceRoot,
    cacheDir: localOverrides?.cacheDir ?? overrides?.cacheDir ?? baseConfig.cacheDir,
  });

  const resolvePaths = (localOverrides?: Partial<MaterialsLabPluginConfig>): MaterialsWorkspacePaths =>
    resolveWorkspacePaths(resolveConfig(localOverrides));

  return {
    logger: createLogger(),
    loadConfigSource: () => source,
    resolveConfig,
    resolvePaths,
    getArtifactService(localOverrides) {
      return new ArtifactService(resolvePaths(localOverrides));
    },
    getNoteService(localOverrides) {
      return new NoteService(this.getArtifactService(localOverrides));
    },
    getBridge() {
      return {
        ping: vi.fn().mockResolvedValue({
          ok: true,
          action: "ping",
          requestId: "ping",
          summary: "Materials Lab worker is ready.",
          data: { worker: "0.1.0", python: "3.12.0" },
        }),
      } as MaterialsPluginContext["getBridge"] extends (...args: never[]) => infer T ? T : never;
    },
    warmup: vi.fn(async () => undefined),
    stop: vi.fn(async () => undefined),
  };
}
