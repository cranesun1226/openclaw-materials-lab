import type { ArtifactService } from "./artifact-service.js";

export interface SaveNoteInput {
  title: string;
  body: string;
  noteType?: "observation" | "assumption" | "decision" | "failed-path" | "todo";
  tags?: string[];
  candidateIds?: string[];
  artifactPaths?: string[];
}

export interface SavedNoteResult {
  path: string;
  createdAt: string;
}

export class NoteService {
  public constructor(private readonly artifactService: ArtifactService) {}

  public async saveNote(input: SaveNoteInput): Promise<SavedNoteResult> {
    const createdAt = new Date().toISOString();
    const notePath = this.artifactService.createNotePath(input.title);
    const frontmatter = [
      "---",
      `title: ${escapeYaml(input.title)}`,
      `createdAt: ${createdAt}`,
      `noteType: ${escapeYaml(input.noteType ?? "observation")}`,
      `tags: [${(input.tags ?? []).map(escapeYaml).join(", ")}]`,
      `candidateIds: [${(input.candidateIds ?? []).map(escapeYaml).join(", ")}]`,
      `artifacts: [${(input.artifactPaths ?? []).map(escapeYaml).join(", ")}]`,
      "---",
      "",
      input.body.trim(),
      "",
    ].join("\n");

    await this.artifactService.writeText(notePath, frontmatter);

    return {
      path: notePath,
      createdAt,
    };
  }
}

function escapeYaml(value: string): string {
  return JSON.stringify(value);
}
