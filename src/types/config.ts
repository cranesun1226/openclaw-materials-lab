export interface MaterialsLabPluginConfig {
  pythonPath: string;
  mpApiKey: string;
  workspaceRoot: string;
  cacheDir: string;
  defaultBatchLimit: number;
  enableAseTools: boolean;
}

export interface MaterialsWorkspacePaths {
  workspaceRoot: string;
  cacheDir: string;
  notesDir: string;
  reportsDir: string;
  plotsDir: string;
  structuresDir: string;
}

export interface MaterialsConfigSource {
  tools?: {
    allow?: string[];
  };
  plugins?: {
    entries?: Record<
      string,
      {
        enabled?: boolean;
        config?: Partial<MaterialsLabPluginConfig>;
      }
    >;
  };
}
