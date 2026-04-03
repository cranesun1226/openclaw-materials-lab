import { writeFile } from "node:fs/promises";
import path from "node:path";

import type { MaterialsWorkspacePaths } from "../types/config.js";
import type { ToolArtifact } from "../types/tool-results.js";
import { ensureWithinRoot, ensureWorkspaceLayout, slugify, timestampId } from "../core/paths.js";

export class ArtifactService {
  public constructor(private readonly paths: MaterialsWorkspacePaths) {}

  public async ensureReady(): Promise<void> {
    await ensureWorkspaceLayout(this.paths);
  }

  public getPaths(): MaterialsWorkspacePaths {
    return this.paths;
  }

  public createStructureArtifactDir(materialId: string): string {
    return ensureWithinRoot(this.paths.structuresDir, path.join(this.paths.structuresDir, slugify(materialId)), "structure dir");
  }

  public createNotePath(title: string): string {
    return ensureWithinRoot(
      this.paths.notesDir,
      path.join(this.paths.notesDir, `${timestampId()}-${slugify(title || "note")}.md`),
      "note path",
    );
  }

  public createReportPath(title: string, explicitName?: string): string {
    const fileName = explicitName?.trim()
      ? `${slugify(explicitName.replace(/\.md$/i, ""))}.md`
      : `${timestampId()}-${slugify(title || "report")}.md`;

    return ensureWithinRoot(this.paths.reportsDir, path.join(this.paths.reportsDir, fileName), "report path");
  }

  public createPlotDir(): string {
    return this.paths.plotsDir;
  }

  public async writeText(targetPath: string, content: string): Promise<string> {
    const safePath = ensureWithinRoot(this.paths.workspaceRoot, targetPath);
    await this.ensureReady();
    await writeFile(safePath, content, "utf8");
    return safePath;
  }

  public async writeJson(targetPath: string, payload: unknown): Promise<string> {
    return this.writeText(targetPath, `${JSON.stringify(payload, null, 2)}\n`);
  }

  public describePath(targetPath: string): ToolArtifact {
    const ext = path.extname(targetPath).toLowerCase();
    const label = path.basename(targetPath);

    if (targetPath.startsWith(this.paths.reportsDir)) {
      return { label, path: targetPath, kind: "report" };
    }

    if (targetPath.startsWith(this.paths.notesDir)) {
      return { label, path: targetPath, kind: "note" };
    }

    if (targetPath.startsWith(this.paths.structuresDir)) {
      return { label, path: targetPath, kind: "structure" };
    }

    if (targetPath.startsWith(this.paths.plotsDir) || [".png", ".svg", ".pdf"].includes(ext)) {
      return { label, path: targetPath, kind: "plot" };
    }

    if (ext === ".json") {
      return { label, path: targetPath, kind: "json" };
    }

    if ([".md", ".txt", ".log"].includes(ext)) {
      return { label, path: targetPath, kind: "text" };
    }

    return { label, path: targetPath, kind: "other" };
  }
}
