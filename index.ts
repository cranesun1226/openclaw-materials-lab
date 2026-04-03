import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";

import { registerMaterialsCli } from "./src/cli/register-materials-cli.js";
import { PLUGIN_DESCRIPTION, PLUGIN_ID, PLUGIN_NAME, createPluginContext } from "./src/core/runtime-context.js";
import { registerMaterialsApprovalHook } from "./src/hooks/approvals.js";
import { registerMaterialsTools } from "./src/tools/index.js";

export default definePluginEntry({
  id: PLUGIN_ID,
  name: PLUGIN_NAME,
  description: PLUGIN_DESCRIPTION,
  register(api) {
    const context = createPluginContext(api);

    api.registerService({
      id: `${PLUGIN_ID}.python-bridge`,
      async start() {
        await context.warmup();
      },
      async stop() {
        await context.stop();
      },
    });

    registerMaterialsTools(api, context);
    registerMaterialsCli(api, context);
    registerMaterialsApprovalHook(api);
  },
});
