import type { OpenClawPluginApi } from "openclaw/plugin-sdk/plugin-entry";

import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { createMaterialsAnalyzeStructureTool } from "./materials-analyze-structure.js";
import { createMaterialsAseRelaxTool } from "./materials-ase-relax.js";
import { createMaterialsBatchScreenTool } from "./materials-batch-screen.js";
import { createMaterialsCompareCandidatesTool } from "./materials-compare-candidates.js";
import { createMaterialsExecuteResearchPlanTool } from "./materials-execute-research-plan.js";
import { createMaterialsEvaluateResearchClaimTool } from "./materials-evaluate-research-claim.js";
import { createMaterialsExportReportTool } from "./materials-export-report.js";
import { createMaterialsFetchStructureTool } from "./materials-fetch-structure.js";
import { createMaterialsIngestEvidenceTool } from "./materials-ingest-evidence.js";
import { createMaterialsPlanResearchLoopTool } from "./materials-plan-research-loop.js";
import { createMaterialsSaveNoteTool } from "./materials-save-note.js";
import { createMaterialsSearchTool } from "./materials-search-mp.js";

export function registerMaterialsTools(api: OpenClawPluginApi, context: MaterialsPluginContext): void {
  api.registerTool(createMaterialsSearchTool(context));
  api.registerTool(createMaterialsFetchStructureTool(context));
  api.registerTool(createMaterialsAnalyzeStructureTool(context));
  api.registerTool(createMaterialsCompareCandidatesTool(context));
  api.registerTool(createMaterialsPlanResearchLoopTool(context));
  api.registerTool(createMaterialsIngestEvidenceTool(context));
  api.registerTool(createMaterialsEvaluateResearchClaimTool(context));
  api.registerTool(createMaterialsSaveNoteTool(context));
  api.registerTool(createMaterialsExportReportTool(context));
  api.registerTool(createMaterialsAseRelaxTool(context), { optional: true });
  api.registerTool(createMaterialsBatchScreenTool(context), { optional: true });
  api.registerTool(createMaterialsExecuteResearchPlanTool(context), { optional: true });
}
