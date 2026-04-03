import type { OpenClawPluginApi } from "openclaw/plugin-sdk/plugin-entry";

import type { MaterialsPluginContext } from "../core/runtime-context.js";
import { registerDoctorCommand } from "./doctor.js";
import { registerSetupPythonCommand } from "./setup-python.js";
import { registerStatusCommand } from "./status.js";

export function registerMaterialsCli(api: OpenClawPluginApi, context: MaterialsPluginContext): void {
  api.registerCli(
    ({ program }) => {
      const materials = program.command("materials").description("Materials Lab setup and diagnostics commands.");
      registerDoctorCommand(materials, context);
      registerSetupPythonCommand(materials, context);
      registerStatusCommand(materials, context);
    },
    { commands: ["materials"] },
  );
}
