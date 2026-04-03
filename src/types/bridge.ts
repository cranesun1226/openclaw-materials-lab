export type BridgeAction =
  | "ping"
  | "search_materials"
  | "fetch_structure"
  | "analyze_structure"
  | "compare_candidates"
  | "ase_relax"
  | "batch_screen"
  | "export_report";

export interface BridgeErrorDetails {
  code: string;
  message: string;
  hint?: string;
  retriable?: boolean;
  details?: unknown;
  stderr?: string;
}

export interface BridgeRequest<TPayload = Record<string, unknown>> {
  action: BridgeAction;
  requestId: string;
  payload: TPayload;
}

export interface BridgeSuccess<TData = unknown> {
  ok: true;
  action: BridgeAction;
  requestId: string;
  summary: string;
  data: TData;
  artifacts?: string[];
  warnings?: string[];
}

export interface BridgeFailure {
  ok: false;
  action?: BridgeAction;
  requestId?: string;
  error: BridgeErrorDetails;
}

export type BridgeResponse<TData = unknown> = BridgeSuccess<TData> | BridgeFailure;

export interface CandidateSummary {
  materialId: string;
  formula: string;
  energyAboveHullEv?: number;
  bandGapEv?: number;
  densityGcm3?: number;
  volume?: number;
  sites?: number;
  spacegroup?: string;
  elements?: string[];
  source: "materials-project" | "mock";
  notes?: string[];
}

export interface SearchMaterialsPayload {
  textQuery?: string;
  formula?: string;
  elementsAll?: string[];
  elementsAny?: string[];
  maxEnergyAboveHullEv?: number;
  minBandGapEv?: number;
  maxBandGapEv?: number;
  limit?: number;
  allowOffline?: boolean;
}

export interface SearchMaterialsResult {
  candidates: CandidateSummary[];
  usedOfflineData: boolean;
}

export interface FetchStructurePayload {
  materialId: string;
  format?: "json" | "cif" | "both";
  artifactDir: string;
  allowOffline?: boolean;
}

export interface FetchStructureResult {
  material: CandidateSummary;
  structurePath?: string;
  cifPath?: string;
  structure?: Record<string, unknown>;
  usedOfflineData: boolean;
}

export interface AnalyzeStructurePayload {
  materialId?: string;
  structurePath?: string;
  structure?: Record<string, unknown>;
  artifactDir: string;
  allowOffline?: boolean;
}

export interface AnalyzeStructureResult {
  materialId?: string;
  formula?: string;
  summaryMetrics: Record<string, number | string | boolean | null>;
  readableSummary: string;
  plotPath?: string;
  usedOfflineData: boolean;
}

export interface CompareCriteria {
  stabilityWeight?: number;
  bandGapWeight?: number;
  densityWeight?: number;
  bandGapTargetEv?: number;
  densityTargetGcm3?: number;
}

export interface CompareCandidatesPayload {
  candidates: CandidateSummary[];
  criteria?: CompareCriteria;
  artifactDir: string;
  topK?: number;
}

export interface ComparedCandidate extends CandidateSummary {
  score: number;
  reasons: string[];
  rank: number;
}

export interface CompareCandidatesResult {
  ranked: ComparedCandidate[];
  criteria: Required<CompareCriteria>;
  plotPath?: string;
}

export interface AseRelaxPayload {
  materialId?: string;
  structurePath?: string;
  artifactDir: string;
  steps?: number;
  fmaxEvA?: number;
  calculator?: string;
  allowOffline?: boolean;
}

export interface AseRelaxResult {
  summaryMetrics: Record<string, number | string | boolean | null>;
  relaxedStructurePath?: string;
  trajectoryPath?: string;
  usedOfflineData: boolean;
}

export interface BatchScreenPayload {
  candidateIds: string[];
  limit: number;
  artifactDir: string;
  allowOffline?: boolean;
}

export interface BatchScreenResult {
  screened: CandidateSummary[];
  ranked: ComparedCandidate[];
  usedOfflineData: boolean;
}

export interface ExportReportPayload {
  title: string;
  goal: string;
  evaluationCriteria: string[];
  rankedCandidates: ComparedCandidate[];
  notePaths?: string[];
  artifactPaths?: string[];
  outputPath: string;
}

export interface ExportReportResult {
  outputPath: string;
  references: string[];
}
