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
  materialsProjectUrl?: string;
  family?: string;
  duplicateGroup?: string;
  duplicateCount?: number;
  warnings?: string[];
  screeningLevel?: string;
  riskProfile?: Record<string, unknown>;
  compositionDescriptors?: Record<string, unknown>;
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
  preset?: "generic" | "solid-electrolyte";
  screeningLevel?: "technical-smoke" | "proxy-screen" | "research-shortlist" | "validated-candidate";
  stabilityWeight?: number;
  bandGapWeight?: number;
  densityWeight?: number;
  bandGapScoringMode?: "target" | "minimum";
  minimumBandGapEv?: number;
  bandGapTargetEv?: number;
  densityScoringMode?: "target" | "advisory" | "none";
  densityTargetGcm3?: number;
  secondaryWeight?: number;
  riskPenaltyWeight?: number;
  preferredBandGapEv?: number;
  preferredLiFractionMin?: number;
  preferredLiFractionMax?: number;
  excludeToxicElements?: boolean;
  excludeRiskyChemistry?: boolean;
  filterMolecularSalts?: boolean;
  requiresLithium?: boolean;
  excludedElements?: string[];
  flaggedElements?: string[];
  maxHydrogenAtomicFraction?: number;
  diversifyBy?: "none" | "formula" | "family" | "formula-and-family";
  maxPerFormula?: number;
  maxPerFamily?: number;
}

export interface CompareCandidatesPayload {
  candidates: CandidateSummary[];
  criteria?: CompareCriteria;
  artifactDir: string;
  topK?: number;
}

export interface ComparedCandidate extends CandidateSummary {
  score: number;
  primaryScore?: number;
  secondaryScore?: number;
  riskPenalty?: number;
  rawRank?: number;
  reasons: string[];
  rank: number;
  scoreComponents?: {
    raw?: Record<string, number>;
    weighted?: Record<string, number>;
  };
}

export interface CompareCandidatesResult {
  ranked: ComparedCandidate[];
  criteria: Required<CompareCriteria>;
  plotPath?: string;
  tablePaths?: string[];
  screeningLevel?: string;
  diversity?: Record<string, unknown>;
  excludedCandidates?: Array<Record<string, unknown>>;
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
  tablePaths?: string[];
  excludedCandidates?: Array<Record<string, unknown>>;
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
  screeningLevel?: string;
  domainWarnings?: string[];
  methodNotes?: string[];
  provenance?: Record<string, unknown>;
}

export interface ExportReportResult {
  outputPath: string;
  references: string[];
}
