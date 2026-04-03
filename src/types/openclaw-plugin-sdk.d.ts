declare module "openclaw/plugin-sdk/plugin-entry" {
  import type { TObject } from "@sinclair/typebox";

  export interface OpenClawToolDefinition<TSchema extends TObject = TObject> {
    name: string;
    description: string;
    parameters: TSchema;
    execute(callId: string, params: unknown): Promise<unknown> | unknown;
  }

  export interface OpenClawServiceDefinition {
    id: string;
    start?: () => Promise<void> | void;
    stop?: () => Promise<void> | void;
  }

  export interface OpenClawCommandProgramLike {
    command(name: string): OpenClawCommandProgramLike;
    description(text: string): OpenClawCommandProgramLike;
    option(flags: string, description: string, defaultValue?: string | number | boolean): OpenClawCommandProgramLike;
    action(handler: (...args: unknown[]) => unknown): OpenClawCommandProgramLike;
  }

  export interface OpenClawCliRegistrationContext {
    program: OpenClawCommandProgramLike;
  }

  export interface OpenClawPluginApi {
    logger?: {
      debug?: (message: string, meta?: unknown) => void;
      info?: (message: string, meta?: unknown) => void;
      warn?: (message: string, meta?: unknown) => void;
      error?: (message: string, meta?: unknown) => void;
    };
    runtime?: {
      config?: {
        loadConfig?: () => unknown;
      };
    };
    registerTool(definition: OpenClawToolDefinition, options?: { optional?: boolean }): void;
    registerService(definition: OpenClawServiceDefinition): void;
    registerCli(
      register: (context: OpenClawCliRegistrationContext) => void,
      options?: { commands?: string[] },
    ): void;
    on?(event: string, handler: (context: unknown) => unknown): void;
  }

  export interface OpenClawPluginEntry {
    id: string;
    name: string;
    description?: string;
    register(api: OpenClawPluginApi): void;
  }

  export function definePluginEntry(entry: OpenClawPluginEntry): OpenClawPluginEntry;
}
