export interface MaterialsCommandProgramLike {
  command(name: string): MaterialsCommandProgramLike;
  description(text: string): MaterialsCommandProgramLike;
  option(flags: string, description?: string, defaultValue?: unknown): MaterialsCommandProgramLike;
  action(handler: (...args: unknown[]) => unknown): MaterialsCommandProgramLike;
}
