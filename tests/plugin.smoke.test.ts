import { describe, expect, it } from "vitest";

import plugin from "../index.js";

class CommandMock {
  public readonly children: CommandMock[] = [];
  public readonly options: string[] = [];
  public descriptionText = "";
  public actionHandler: ((...args: unknown[]) => unknown) | undefined;

  public constructor(public readonly name: string) {}

  public command(name: string): CommandMock {
    const child = new CommandMock(name);
    this.children.push(child);
    return child;
  }

  public description(text: string): this {
    this.descriptionText = text;
    return this;
  }

  public option(flags: string): this {
    this.options.push(flags);
    return this;
  }

  public action(handler: (...args: unknown[]) => unknown): this {
    this.actionHandler = handler;
    return this;
  }
}

describe("plugin registration", () => {
  it("registers services, tools, CLI, and approval hooks", () => {
    const toolRegistrations: Array<{ name: string; optional: boolean }> = [];
    const services: string[] = [];
    const cliCommands: string[][] = [];
    const hooks: string[] = [];
    const program = new CommandMock("root");

    plugin.register({
      logger: {},
      runtime: {
        config: {
          loadConfig: () => ({
            plugins: {
              entries: {
                "materials-lab": {
                  config: {
                    pythonPath: "python3",
                    workspaceRoot: "/tmp/materials-lab",
                    cacheDir: "/tmp/materials-lab/cache",
                  },
                },
              },
            },
          }),
        },
      },
      registerTool(definition, options) {
        toolRegistrations.push({ name: definition.name, optional: Boolean(options?.optional) });
      },
      registerService(definition) {
        services.push(definition.id);
      },
      registerCli(register, options) {
        register({ program });
        cliCommands.push(options?.commands ?? []);
      },
      on(event) {
        hooks.push(event);
      },
    });

    expect(plugin.id).toBe("materials-lab");
    expect(services).toContain("materials-lab.python-bridge");
    expect(toolRegistrations).toEqual(
      expect.arrayContaining([
        { name: "materials_search_mp", optional: false },
        { name: "materials_fetch_structure", optional: false },
        { name: "materials_analyze_structure", optional: false },
        { name: "materials_compare_candidates", optional: false },
        { name: "materials_save_note", optional: false },
        { name: "materials_export_report", optional: false },
        { name: "materials_ase_relax", optional: true },
        { name: "materials_batch_screen", optional: true },
      ]),
    );
    expect(cliCommands).toContainEqual(["materials"]);
    expect(hooks).toContain("before_tool_call");

    const materialsRoot = program.children.find((child) => child.name === "materials");
    expect(materialsRoot).toBeDefined();
    expect(materialsRoot?.children.map((child) => child.name)).toEqual(
      expect.arrayContaining(["doctor", "setup-python", "status"]),
    );
  });
});
