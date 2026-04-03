import { mkdir, access } from "node:fs/promises";
import { constants as fsConstants } from "node:fs";
import path from "node:path";
import os from "node:os";

import type { MaterialsLabPluginConfig, MaterialsWorkspacePaths } from "../types/config.js";
import { PathValidationError } from "./errors.js";

const WORKSPACE_CHILDREN = {
  notesDir: "notes",
  reportsDir: "reports",
  plotsDir: "plots",
  structuresDir: "structures",
  cacheDir: "cache",
} satisfies Record<string, string>;

export function expandHome(input: string): string {
  if (input.startsWith("~/")) {
    return path.join(os.homedir(), input.slice(2));
  }

  return input;
}

export function resolveWorkspacePaths(config: MaterialsLabPluginConfig): MaterialsWorkspacePaths {
  const workspaceRoot = path.resolve(expandHome(config.workspaceRoot));
  const cacheDir = config.cacheDir
    ? path.resolve(expandHome(config.cacheDir))
    : path.join(workspaceRoot, WORKSPACE_CHILDREN.cacheDir);

  return {
    workspaceRoot,
    cacheDir,
    notesDir: path.join(workspaceRoot, WORKSPACE_CHILDREN.notesDir),
    reportsDir: path.join(workspaceRoot, WORKSPACE_CHILDREN.reportsDir),
    plotsDir: path.join(workspaceRoot, WORKSPACE_CHILDREN.plotsDir),
    structuresDir: path.join(workspaceRoot, WORKSPACE_CHILDREN.structuresDir),
  };
}

export async function ensureWorkspaceLayout(paths: MaterialsWorkspacePaths): Promise<void> {
  await mkdir(paths.workspaceRoot, { recursive: true });
  await Promise.all(
    Object.values(paths).map(async (dir) => {
      await mkdir(dir, { recursive: true });
    }),
  );
}

export async function assertWritableDirectory(directory: string): Promise<void> {
  await mkdir(directory, { recursive: true });
  await access(directory, fsConstants.W_OK);
}

export function ensureWithinRoot(root: string, candidatePath: string, label = "path"): string {
  const resolvedRoot = path.resolve(root);
  const resolvedCandidate = path.resolve(candidatePath);
  const relative = path.relative(resolvedRoot, resolvedCandidate);

  if (relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative))) {
    return resolvedCandidate;
  }

  throw new PathValidationError(`${label} must stay inside ${resolvedRoot}`, {
    hint: "Update the plugin workspace configuration or choose a destination under workspaceRoot.",
    details: { root: resolvedRoot, candidate: resolvedCandidate },
  });
}

export function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64);
}

export function timestampId(date = new Date()): string {
  return date.toISOString().replace(/[:.]/g, "-");
}
