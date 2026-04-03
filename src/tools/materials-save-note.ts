import { Type, type Static } from "@sinclair/typebox";
import type { AnyAgentTool } from "openclaw/plugin-sdk/plugin-entry";

import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { toToolResponse } from "../types/tool-results.js";

const SaveNoteSchema = Type.Object(
  {
    title: Type.String({ minLength: 1, maxLength: 160 }),
    body: Type.String({ minLength: 1 }),
    noteType: Type.Optional(
      Type.Union([
        Type.Literal("observation"),
        Type.Literal("assumption"),
        Type.Literal("decision"),
        Type.Literal("failed-path"),
        Type.Literal("todo"),
      ]),
    ),
    tags: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 40 }), { maxItems: 20 })),
    candidateIds: Type.Optional(Type.Array(Type.String({ minLength: 1, maxLength: 80 }), { maxItems: 20 })),
    artifactPaths: Type.Optional(Type.Array(Type.String({ minLength: 1 }), { maxItems: 50 })),
  },
  { additionalProperties: false },
);

export type MaterialsSaveNoteParams = Static<typeof SaveNoteSchema>;

export function createMaterialsSaveNoteTool(context: MaterialsPluginContext): AnyAgentTool {
  return {
    name: "materials_save_note",
    label: "Save Note",
    description: "Persist a structured research note under the plugin workspaceRoot.",
    parameters: SaveNoteSchema,
    async execute(_callId, rawParams) {
      const params = rawParams as MaterialsSaveNoteParams;
      const artifactService = context.getArtifactService();
      await artifactService.ensureReady();
      const saved = await context.getNoteService().saveNote(params);
      const artifact = artifactService.describePath(saved.path);

      return toToolResponse({
        summary: `Saved note "${params.title}" to ${saved.path}.`,
        data: {
          path: saved.path,
          createdAt: saved.createdAt,
          title: params.title,
          noteType: params.noteType ?? "observation",
        },
        artifacts: [artifact],
        warnings: [],
      });
    },
  };
}
