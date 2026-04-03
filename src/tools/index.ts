import type { OpenClawPluginApi } from "openclaw/plugin-sdk/plugin-entry";

import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { createMaterialsAnalyzeStructureTool } from "./materials-analyze-structure.js";
import { createMaterialsAseRelaxTool } from "./materials-ase-relax.js";
import { createMaterialsBatchScreenTool } from "./materials-batch-screen.js";
import { createMaterialsCompareCandidatesTool } from "./materials-compare-candidates.js";
import { createMaterialsExportReportTool } from "./materials-export-report.js";
import { createMaterialsFetchStructureTool } from "./materials-fetch-structure.js";
import { createMaterialsSaveNoteTool } from "./materials-save-note.js";
import { createMaterialsSearchTool } from "./materials-search-mp.js";

export function registerMaterialsTools(api: OpenClawPluginApi, context: MaterialsPluginContext): void {
  api.registerTool(createMaterialsSearchTool(context));
  api.registerTool(createMaterialsFetchStructureTool(context));
  api.registerTool(createMaterialsAnalyzeStructureTool(context));
  api.registerTool(createMaterialsCompareCandidatesTool(context));
  api.registerTool(createMaterialsSaveNoteTool(context));
  api.registerTool(createMaterialsExportReportTool(context));
  api.registerTool(createMaterialsAseRelaxTool(context), { optional: true });
  api.registerTool(createMaterialsBatchScreenTool(context), { optional: true });
}
